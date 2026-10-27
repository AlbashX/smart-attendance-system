import base64
import io
import numpy as np
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from backend import main
from backend.store import Store


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, 'store', Store(tmp_path / 'test.db'))
    main.pending.clear()
    main.stability.clear()
    return TestClient(main.app)


def fake_face(monkeypatch, vector=None):
    vector = vector or [1., 0.]
    monkeypatch.setattr(main.engine, 'extract', lambda image: dict(
        embedding=vector, quality=True, face_count=1, latency_ms=12,
        reason='Face quality passed', box=[0, 0, 100, 100], width=640, height=480))


def enroll(client, monkeypatch):
    """Create a student, capture samples and save enrollment."""
    fake_face(monkeypatch)
    # Create the student first
    r = client.post('/api/students', json={
        'name': 'Student A', 'roll_no': 'D-1', 'section': 'D', 'batch': 'D1'
    })
    sid = r.json()['id']
    # Capture enrollment samples
    tokens = [
        client.post(f'/api/students/{sid}/enrollment/sample',
                    json={'image': 'mock', 'consent': True}).json()['token']
        for _ in range(5)
    ]
    # Save enrollment
    client.post(f'/api/students/{sid}/enrollment/save',
                json={'consent': True, 'tokens': tokens})
    return sid


def test_enrollment_consent_and_unique_tokens(client, monkeypatch):
    fake_face(monkeypatch)
    # Create student
    sid = client.post('/api/students', json={
        'name': 'A', 'roll_no': 'T1', 'section': 'D'
    }).json()['id']
    # Consent False should be rejected
    assert client.post(f'/api/students/{sid}/enrollment/sample',
                       json={'image': 'mock', 'consent': False}).status_code == 422
    token = client.post(f'/api/students/{sid}/enrollment/sample',
                        json={'image': 'mock', 'consent': True}).json()['token']
    # Duplicate tokens should fail
    body = {'consent': True, 'tokens': [token] * 5}
    assert client.post(f'/api/students/{sid}/enrollment/save',
                       json=body).status_code == 400
    # Full enrollment should succeed
    sid2 = enroll(client, monkeypatch)
    assert sid2 is not None
    students = client.get('/api/state').json()['students']
    assert any(s['sample_count'] > 0 for s in students)


def test_recognition_requires_stability_and_rejects_unknown(client, monkeypatch):
    sid = enroll(client, monkeypatch)
    session_id = client.post('/api/sessions', json={'name': 'Test'}).json()['id']
    body = {'image': 'mock', 'session_id': session_id, 'stream_id': 'test'}
    assert not client.post('/api/recognize', json=body).json()['marked']
    assert not client.post('/api/recognize', json=body).json()['marked']
    assert client.post('/api/recognize', json=body).json()['marked']
    assert not client.post('/api/recognize', json=body).json()['marked']
    assert len(main.store.records(session_id=session_id)) >= 1
    fake_face(monkeypatch, [-1., 0.])
    result = client.post('/api/recognize', json=body).json()
    assert result['identity'] is None and not result['stable']
    assert 'embedding' not in result


def test_calibration_freezes_validation_and_requires_separate_test_batch(client, monkeypatch):
    sid = enroll(client, monkeypatch)
    body = {'image': 'mock', 'consent': True, 'split': 'validation',
            'subject': 'known', 'batch': 'validation-day', 'expected': sid}
    for _ in range(5):
        assert client.post('/api/probes', json=body).status_code == 200
    fake_face(monkeypatch, [0., 1.])
    body.update(expected=None, subject='unknown-A')
    for _ in range(5):
        assert client.post('/api/probes', json=body).status_code == 200
    assert client.post('/api/calibrate').status_code == 200
    assert client.post('/api/probes', json=body).status_code == 400
    body['split'] = 'test'
    assert client.post('/api/probes', json=body).status_code == 400
    body.update(batch='test-day', subject='unknown-B')
    assert client.post('/api/probes', json=body).status_code == 200
    assert client.get('/api/evaluation').json()['test']['unknown_rejection_accuracy'] == 1
    client.delete(f'/api/students/{sid}')
    assert not client.get('/api/state').json()['settings']['calibrated']
    assert client.get('/api/evaluation').json()['test']['attempts'] == 0


def test_invalid_image_and_cross_origin_are_rejected(client):
    assert client.post('/api/recognize',
                       json={'image': 'not-an-image'}).status_code == 400
    assert client.post('/api/sessions', json={'name': 'A'},
                       headers={'Origin': 'https://evil.example'}).status_code == 403
    assert client.get('/api/state',
                      headers={'Host': 'evil.example'}).status_code == 400


def test_real_model_blank_image_rejected(client):
    buffer = io.BytesIO()
    Image.new('RGB', (640, 480), (120, 120, 120)).save(buffer, format='JPEG')
    result = client.post('/api/recognize',
                         json={'image': base64.b64encode(buffer.getvalue()).decode()})
    assert result.status_code == 200
    assert result.json()['face_count'] == 0
    assert not result.json()['marked']


def test_real_sface_forward_pass_produces_finite_embedding():
    # A synthetic crop checks ONNX/runtime compatibility, not biometric accuracy.
    from backend.vision import FaceEngine
    from backend.core import normalize
    engine = FaceEngine()
    engine.load()
    crop = np.random.default_rng(42).integers(0, 256, (112, 112, 3), dtype=np.uint8)
    vector = normalize(engine.recognizer.feature(crop))
    assert vector.shape == (128,)
    assert np.isfinite(vector).all()
    assert np.linalg.norm(vector) == pytest.approx(1)


def test_closed_session_cannot_receive_attendance(client, monkeypatch):
    sid = enroll(client, monkeypatch)
    session_id = main.store.start_session('A')
    main.store.end_session(session_id)
    with pytest.raises(ValueError):
        main.store.mark(sid, session_id, .9)


def test_csv_formula_escape(client, monkeypatch):
    pid = main.store.add_student('=FORMULA', '+123', email=None, section='D')
    sid = main.store.start_session('@SESSION')
    main.store.mark(pid, sid, .9)
    csv = client.get('/api/attendance.csv').text
    assert "'=FORMULA" in csv and "'+123" in csv and "'@SESSION" in csv


def test_cross_batch_attendance_rejected(client, monkeypatch):
    """Students from batch D3 must not be marked present in a batch D1 session."""
    s1 = main.store.add_student('D-1', 'Student D1', batch='D1')
    s3 = main.store.add_student('D-52', 'Student D3', batch='D3')
    rid = main.store.add_timetable_rule(1, '15:00', '17:00', 'Cloud Lab', batch='D1')
    sess_id = main.store.start_session('Cloud Lab (D1)', rule_id=rid)

    # Student from batch D3 must be rejected
    assert main.store.mark(s3, sess_id, 0.9) is False
    # Student from batch D1 must be accepted
    assert main.store.mark(s1, sess_id, 0.9) is True

