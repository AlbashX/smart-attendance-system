import csv
import io
import ipaddress
import json
import os
import sqlite3
import threading
import time
import uuid
from datetime import datetime, date
from pathlib import Path
from typing import Literal
import numpy as np
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .core import normalize, match, Stability, calibrate, verification_metrics
from .store import Store, now
from .vision import FaceEngine

ROOT = Path(__file__).resolve().parents[1]
store = Store(os.environ.get('ATTEND_DB', str(ROOT / 'data/attendance.db')))
engine = FaceEngine()
app = FastAPI(title='Attend — Classroom Attendance API', version='0.2.0')
# One process/worker: session stability and ephemeral enrollment tokens are in memory.
lock = threading.RLock()
pending = {}
stability = {}


def _local_hostname(host_header: str) -> str:
    host = (host_header or '').strip()
    if host.startswith('['):
        end = host.find(']')
        return host[1:end] if end != -1 else host
    return host.split(':')[0]


def _allow_local_host(host_header: str) -> bool:
    hostname = _local_hostname(host_header).lower()
    if hostname in {'localhost', '127.0.0.1', '::1', 'testserver'} or hostname.endswith('.local'):
        return True
    try:
        return ipaddress.ip_address(hostname).is_private
    except ValueError:
        return False


@app.middleware('http')
async def require_local_host(request: Request, call_next):
    if not _allow_local_host(request.headers.get('host', '')):
        return JSONResponse({'detail': 'Host not allowed'}, status_code=400)
    return await call_next(request)

DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']


@app.middleware('http')
async def local_only(request: Request, call_next):
    origin = request.headers.get('origin')
    if origin and origin != str(request.base_url).rstrip('/'):
        return JSONResponse({'detail': 'Cross-origin access is disabled'}, status_code=403)
    if int(request.headers.get('content-length', '0')) > 10_000_000:
        return JSONResponse({'detail': 'Request too large'}, status_code=413)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; img-src 'self' data:; media-src 'self' blob:; "
        "style-src 'self' 'unsafe-inline'; script-src 'self'; "
        "connect-src 'self'; frame-ancestors 'none'")
    return response


@app.exception_handler(ValueError)
async def value_error(request, error):
    return JSONResponse({'detail': str(error)}, status_code=400)


@app.exception_handler(sqlite3.IntegrityError)
async def db_error(request, error):
    return JSONResponse(
        {'detail': 'That roll number already exists, or the record conflicts '
                    'with current data.'},
        status_code=409)


# ── Pydantic models ──────────────────────────────────────────

class Frame(BaseModel):
    image: str = Field(max_length=3_000_000)
    stream_id: str = Field(default='preview', max_length=80)
    session_id: str | None = Field(default=None, max_length=80)


class StudentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    roll_no: str = Field(min_length=1, max_length=40)
    email: str | None = Field(default=None, max_length=120)
    section: str = Field(default='D', max_length=10)
    batch: str | None = Field(default=None, max_length=10)


class EnrollmentSave(BaseModel):
    consent: Literal[True]
    tokens: list[str] = Field(min_length=5, max_length=20)


class ConsentFrame(Frame):
    consent: Literal[True]


class Session(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    rule_id: str | None = None
    date: str | None = None


class TimetableRuleUpdate(BaseModel):
    weekday: int | None = None
    start_time: str | None = None
    end_time: str | None = None
    course_name: str | None = None
    course_code: str | None = None
    teacher: str | None = None
    room: str | None = None
    batch: str | None = None
    is_lab: bool | None = None


class TimetableException(BaseModel):
    rule_id: str
    date: str
    action: Literal['cancel', 'replace'] = 'cancel'
    replacement: dict | None = None
    reason: str | None = None


class Probe(Frame):
    split: Literal['validation', 'test']
    subject: str = Field(min_length=1, max_length=80)
    batch: str = Field(min_length=1, max_length=80)
    expected: str | None = None
    consent: Literal[True]


# ── Helpers ───────────────────────────────────────────────────

def settings():
    return store.setting('calibration',
                         {'threshold': .45, 'margin': .08, 'calibrated': False})


def get_current_classes():
    """Determine all classes currently in session based on the timetable."""
    today = datetime.now()
    weekday = today.weekday()  # 0=Mon..6=Sun
    if weekday > 5:
        return []
    current_time = today.strftime('%H:%M')
    date_str = today.strftime('%Y-%m-%d')
    schedule = store.today_schedule(weekday, date_str)
    return [rule for rule in schedule
            if rule['start_time'] <= current_time < rule['end_time']]


def get_current_session_info():
    """Determine what class should be happening right now based on timetable."""
    classes = get_current_classes()
    return classes[0] if classes else None


def get_next_class():
    """Find the next upcoming class today."""
    today = datetime.now()
    weekday = today.weekday()
    if weekday > 5:
        return None
    current_time = today.strftime('%H:%M')
    date_str = today.strftime('%Y-%m-%d')
    schedule = store.today_schedule(weekday, date_str)
    for rule in schedule:
        if rule['start_time'] > current_time:
            return rule
    return None


def compute_dl_metrics():
    cfg = settings()
    threshold = float(cfg['threshold'])
    margin = float(cfg['margin'])
    students = [s for s in store.students(True) if s.get('centroid')]
    stats = {}
    n = len(students)
    if n > 0:
        centroids = np.array([s['centroid'] for s in students], dtype=np.float32)
        sim_matrix = np.clip(centroids @ centroids.T, -1.0, 1.0)
        impostor_scores = []
        for i, s in enumerate(students):
            other_scores = [float(sim_matrix[i, j]) for j in range(n) if j != i]
            max_imp = max(other_scores) if other_scores else 0.0
            avg_imp = float(np.mean(other_scores)) if other_scores else 0.0
            impostor_scores.extend(other_scores)
            stats[s['id']] = {
                'max_impostor': round(max_imp, 4),
                'avg_impostor': round(avg_imp, 4),
                'margin_to_threshold': round(threshold - max_imp, 4),
                'validation_pass': bool(max_imp < threshold),
                'self_similarity': 1.0,
                'sample_count': s.get('sample_count', 0),
            }
        max_imp_overall = max(impostor_scores) if impostor_scores else 0.0
        avg_imp_overall = float(np.mean(impostor_scores)) if impostor_scores else 0.0
        far = float(np.mean([s >= threshold for s in impostor_scores])) if impostor_scores else 0.0
        acc = float(np.mean([s < threshold for s in impostor_scores])) if impostor_scores else 1.0
    else:
        max_imp_overall = 0.0
        avg_imp_overall = 0.0
        far = 0.0
        acc = 1.0

    eval_data = store.probes()
    val_rows = [r for r in eval_data if r['split'] == 'validation']
    test_rows = [r for r in eval_data if r['split'] == 'test']

    return {
        'model_detector': 'YuNet 2023mar (ONNX)',
        'model_recognizer': 'SFace 2021dec (128-d L2)',
        'embedding_dims': 128,
        'distance_metric': 'Cosine Similarity',
        'threshold': threshold,
        'margin': margin,
        'calibrated': bool(cfg['calibrated']),
        'total_enrolled': n,
        'max_impostor_similarity': round(max_imp_overall, 4) if n > 1 else None,
        'avg_impostor_similarity': round(avg_imp_overall, 4),
        'gallery_separation_rate': round(acc, 4) if n > 1 else None,
        'pairwise_far': round(far, 4),
        'validation_attempts': len(val_rows),
        'test_attempts': len(test_rows),
        'student_metrics': stats,
    }


# ── State endpoint ────────────────────────────────────────────

@app.get('/api/state')
def state():
    models_ready = all(
        (ROOT / 'models' / f).exists()
        for f in ('face_detection_yunet_2023mar.onnx',
                  'face_recognition_sface_2021dec.onnx'))
    active = store.active_session()
    current_classes = get_current_classes()
    if active and active.get('rule_id'):
        matched_rule = next((r for r in store.timetable_rules()
                             if r['id'] == active['rule_id']), None)
        current_class = matched_rule or (current_classes[0] if current_classes else None)
    else:
        current_class = current_classes[0] if current_classes else None
    next_class = get_next_class() if not current_classes else None
    return dict(
        students=store.students(),
        sessions=store.sessions(),
        records=store.all_records(),
        settings=settings(),
        models_ready=models_ready,
        timetable=store.timetable_rules(),
        exceptions=store.timetable_exceptions(),
        active_session=active,
        current_class=current_class,
        current_classes=current_classes,
        next_class=next_class,
        dl_metrics=compute_dl_metrics(),
        today=datetime.now().strftime('%Y-%m-%d'),
        weekday=datetime.now().weekday(),
        day_name=DAY_NAMES[datetime.now().weekday()]
        if datetime.now().weekday() < 6 else 'Sunday'
    )


# ── Student endpoints ────────────────────────────────────────

@app.get('/api/students')
def list_students():
    return store.students()


@app.post('/api/students')
def create_student(body: StudentCreate):
    if not body.name.strip() or not body.roll_no.strip():
        raise ValueError('Name and roll number are required')
    pid = store.add_student(
        roll_no=body.roll_no.strip(),
        name=body.name.strip(),
        email=body.email.strip() if body.email else None,
        section=body.section.strip(),
        batch=body.batch.strip() if body.batch else None,
    )
    return {'id': pid}


@app.delete('/api/students/{sid}')
def remove_student(sid: str):
    with lock:
        store.delete_student(sid)
        stability.clear()
    return {'ok': True}


@app.post('/api/students/{sid}/enrollment/sample')
def enrollment_sample(sid: str, body: ConsentFrame):
    """Capture a single enrollment sample for a student."""
    with lock:
        # Verify student exists
        store.get_student(sid)
        result = engine.extract(body.image)
        embedding = result.pop('embedding', None)
        if embedding is not None:
            stamp = time.monotonic()
            for key in list(pending):
                if stamp - pending[key][0] > 600:
                    del pending[key]
            if len(pending) >= 200:
                raise ValueError(
                    'Too many pending samples. Wait ten minutes or restart.')
            token = str(uuid.uuid4())
            pending[token] = (stamp, embedding)
            result['token'] = token
        return result


@app.post('/api/students/{sid}/enrollment/save')
def enrollment_save(sid: str, body: EnrollmentSave):
    """Save enrollment embeddings for a student."""
    with lock:
        store.get_student(sid)
        if len(set(body.tokens)) != len(body.tokens):
            raise ValueError('Capture distinct samples')
        if any(t not in pending or time.monotonic() - pending[t][0] > 600
               for t in body.tokens):
            raise ValueError('Enrollment captures expired. Capture again.')
        vectors = [pending[t][1] for t in body.tokens]
        centroid = normalize(np.mean(vectors, axis=0))
        if min(float(np.dot(v, centroid)) for v in vectors) < .45:
            raise ValueError(
                'Samples are inconsistent. Capture the same person in even '
                'lighting.')
        # Check for duplicate enrollment
        gallery = {s['id']: s['centroid']
                   for s in store.students(True) if s.get('centroid')}
        if match(centroid, gallery, .65, 0)['identity']:
            raise ValueError(
                'These samples closely match an enrolled student. '
                'Check for duplicate enrollment.')
        store.update_student_enrollment(sid, vectors, centroid.tolist())
        for t in body.tokens:
            del pending[t]
        stability.clear()
    return {'ok': True}


@app.post('/api/students/{sid}/upload')
async def upload_enrollment(sid: str, file: UploadFile = File(...),
                            consent: str = Form('true')):
    """Upload photo(s) or video for enrollment from device."""
    if consent.lower() != 'true':
        raise ValueError('Consent is required')
    with lock:
        store.get_student(sid)
    content = await file.read()
    if len(content) > 10_000_000:
        raise ValueError('File too large. Maximum 10 MB.')

    import base64
    content_type = file.content_type or ''

    if content_type.startswith('video/'):
        # Extract frames from video
        vectors = _extract_from_video(content)
    else:
        # Treat as image
        encoded = base64.b64encode(content).decode()
        result = engine.extract(encoded)
        embedding = result.pop('embedding', None)
        if embedding is None:
            raise ValueError(result.get('reason', 'No face detected in image'))
        vectors = [embedding]

    if len(vectors) < 1:
        raise ValueError('No usable face frames found in the uploaded file.')

    centroid = normalize(np.mean(vectors, axis=0))
    if len(vectors) > 1:
        min_sim = min(float(np.dot(v, centroid)) for v in vectors)
        if min_sim < .4:
            raise ValueError(
                'Frames are too inconsistent. Use a clearer video of one person.')

    with lock:
        gallery = {s['id']: s['centroid']
                   for s in store.students(True) if s.get('centroid')}
        existing_match = match(centroid, gallery, .65, 0)['identity']
        if existing_match and existing_match != sid:
            raise ValueError(
                'This face closely matches another enrolled student.')
        store.update_student_enrollment(sid, vectors, centroid.tolist())
        stability.clear()

    return {'ok': True, 'samples': len(vectors)}


def _extract_from_video(content: bytes):
    """Extract face embeddings from video bytes by sampling frames."""
    import tempfile
    import cv2 as cv

    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        cap = cv.VideoCapture(tmp_path)
        if not cap.isOpened():
            raise ValueError('Cannot open video file')

        fps = cap.get(cv.CAP_PROP_FPS) or 30
        total = int(cap.get(cv.CAP_PROP_FRAME_COUNT))
        duration = total / fps if fps > 0 else 0
        if duration > 60:
            raise ValueError('Video must be 60 seconds or shorter.')

        # Sample one frame every second
        sample_interval = max(1, int(fps))
        vectors = []
        frame_idx = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % sample_interval == 0:
                import base64
                _, buf = cv.imencode('.jpg', frame)
                encoded = base64.b64encode(buf.tobytes()).decode()
                try:
                    result = engine.extract(encoded)
                    emb = result.get('embedding')
                    if emb is not None:
                        vectors.append(emb)
                except Exception:
                    pass
                if len(vectors) >= 15:
                    break
            frame_idx += 1
        cap.release()
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return vectors


# ── Legacy enrollment endpoint (kept for backward compat) ────

@app.post('/api/enrollment/sample')
def sample(body: ConsentFrame):
    with lock:
        result = engine.extract(body.image)
        embedding = result.pop('embedding', None)
        if embedding is not None:
            stamp = time.monotonic()
            for key in list(pending):
                if stamp - pending[key][0] > 600:
                    del pending[key]
            if len(pending) >= 200:
                raise ValueError(
                    'Too many pending samples. Wait ten minutes or restart.')
            token = str(uuid.uuid4())
            pending[token] = (stamp, embedding)
            result['token'] = token
        return result


# ── Session endpoints ─────────────────────────────────────────

@app.post('/api/sessions')
def start_session(body: Session):
    if not body.name.strip():
        raise ValueError('Enter a session name')
    with lock:
        today = body.date or datetime.now().strftime('%Y-%m-%d')
        sid = store.start_session(body.name.strip(), body.rule_id, today)
        stability.clear()
    return {'id': sid}


@app.post('/api/sessions/{sid}/end')
def end_session(sid: str):
    with lock:
        # Mark absent remaining students for this session
        session = store.active_session()
        if session and session['id'] == sid and session.get('rule_id'):
            # Find eligible students based on the timetable rule
            rule = None
            for r in store.timetable_rules():
                if r['id'] == session['rule_id']:
                    rule = r
                    break
            if rule:
                all_students = store.students()
                if rule.get('batch') and rule['batch'] in ('D1', 'D2', 'D3'):
                    eligible = [s['id'] for s in all_students
                                if s['batch'] == rule['batch']]
                else:
                    eligible = [s['id'] for s in all_students]
                store.mark_absent_remaining(sid, eligible)
        store.end_session(sid)
        stability.clear()
    return {'ok': True}


# ── Recognition endpoint ─────────────────────────────────────

@app.post('/api/recognize')
def recognize(body: Frame):
    with lock:
        result = engine.extract(body.image)
        embedding = result.pop('embedding', None)
        students = store.students(True)
        gallery = {s['id']: s['centroid']
                   for s in students if s.get('centroid')}
        config = settings()
        decision = (match(embedding, gallery, config['threshold'],
                          config['margin'])
                    if embedding else
                    dict(identity=None, score=None, gap=None))
        decision.pop('scores', None)
        key = (body.stream_id, body.session_id)
        if len(stability) > 100:
            stability.clear()
        stab_obj = stability.setdefault(key, Stability())
        stable = stab_obj.observe(decision['identity'], time.monotonic())
        stable_count = getattr(stab_obj, 'count', 0)
        marked = False
        if stable and body.session_id:
            marked = store.mark(
                decision['identity'], body.session_id, decision['score'])
        name = next((s['name'] for s in students
                     if s['id'] == decision['identity']), None)
        roll = next((s['roll_no'] for s in students
                     if s['id'] == decision['identity']), None)
        return {**result, **decision,
                'stable': stable, 'marked': marked,
                'name': name, 'roll_no': roll,
                'stable_count': min(stable_count, 3),
                'threshold': config['threshold'],
                'margin': config['margin'],
                'embedding_dim': 128 if embedding is not None else None}


# ── Timetable endpoints ──────────────────────────────────────

@app.get('/api/timetable')
def get_timetable():
    return store.timetable_rules()


@app.get('/api/timetable/today')
def timetable_today():
    today = datetime.now()
    weekday = today.weekday()
    if weekday > 5:
        return {'schedule': [], 'day': 'Sunday', 'date': today.strftime('%Y-%m-%d')}
    date_str = today.strftime('%Y-%m-%d')
    schedule = store.today_schedule(weekday, date_str)
    return {'schedule': schedule, 'day': DAY_NAMES[weekday], 'date': date_str}


@app.put('/api/timetable/{rid}')
def update_timetable(rid: str, body: TimetableRuleUpdate):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    store.update_timetable_rule(rid, **updates)
    return {'ok': True}


@app.post('/api/timetable/exceptions')
def add_exception(body: TimetableException):
    eid = store.add_timetable_exception(
        rule_id=body.rule_id,
        date=body.date,
        action=body.action,
        replacement=body.replacement,
        reason=body.reason
    )
    return {'id': eid}


@app.delete('/api/timetable/exceptions/{eid}')
def remove_exception(eid: str):
    store.delete_timetable_exception(eid)
    return {'ok': True}


# ── Attendance endpoints ──────────────────────────────────────

@app.get('/api/attendance')
def get_attendance(date: str | None = None, session_id: str | None = None):
    return store.records(session_id=session_id, date=date)


@app.get('/api/attendance.csv')
def export_attendance(date: str | None = None, session_id: str | None = None):
    records = store.records(session_id=session_id, date=date)
    out = io.StringIO(newline='')
    fields = ['student_name', 'roll_no', 'section', 'session_name',
              'marked_at', 'status']
    writer = csv.DictWriter(out, fieldnames=fields, extrasaction='ignore')
    writer.writeheader()
    for row in records:
        # Prevent spreadsheet formula interpretation of user-supplied data.
        safe = {k: ("'" + v if isinstance(v, str) and
                     v.startswith(('=', '+', '-', '@', '\t', '\r')) else v)
                for k, v in row.items()}
        writer.writerow(safe)
    return Response(out.getvalue(), media_type='text/csv',
                    headers={'Content-Disposition':
                             'attachment; filename="attendance.csv"'})


# ── Legacy CSV export ─────────────────────────────────────────

@app.get('/api/records.csv')
def export_records():
    out = io.StringIO(newline='')
    fields = ['name', 'student_id', 'session_name', 'marked_at', 'similarity',
              'status']
    writer = csv.DictWriter(out, fieldnames=fields, extrasaction='ignore')
    writer.writeheader()
    for row in store.all_records():
        safe = {k: ("'" + v if isinstance(v, str) and
                     v.startswith(('=', '+', '-', '@', '\t', '\r')) else v)
                for k, v in row.items()}
        writer.writerow(safe)
    return Response(out.getvalue(), media_type='text/csv',
                    headers={'Content-Disposition':
                             'attachment; filename="attendance.csv"'})


# ── Evaluation / Accuracy Lab ─────────────────────────────────

@app.post('/api/probes')
def add_probe(body: Probe):
    with lock:
        config = settings()
        if body.split == 'test' and not config['calibrated']:
            raise ValueError(
                'Calibrate using validation attempts before collecting '
                'the held-out test set')
        if body.split == 'validation' and config['calibrated']:
            raise ValueError(
                'Validation is frozen after calibration. '
                'Reset the experiment to collect more.')
        students = store.students(True)
        if not students:
            raise ValueError('Enroll students before evaluating')
        if body.expected and body.expected not in {s['id'] for s in students}:
            raise ValueError('Student not found')
        if not body.subject.strip() or not body.batch.strip():
            raise ValueError('Subject code and capture batch are required')
        result = engine.extract(body.image)
        embedding = result.pop('embedding', None)
        if embedding is None:
            raise ValueError(result['reason'])
        gallery = {s['id']: s['centroid']
                   for s in students if s.get('centroid')}
        scores = match(embedding, gallery)['scores']
        store.add_probe(body.split, body.subject.strip(), body.batch.strip(),
                        body.expected, scores, result['latency_ms'])
        return result


def evaluate(rows, threshold, margin):
    known = [r for r in rows if r['expected']]
    unknown = [r for r in rows if not r['expected']]
    genuine, impostor = [], []
    correct = wrong = rejected = unknown_correct = 0
    for r in rows:
        ranked = sorted(r['scores'].items(), key=lambda x: x[1], reverse=True)
        best, score = ranked[0]
        gap = score - ranked[1][1] if len(ranked) > 1 else 2
        prediction = best if score >= threshold and gap >= margin else None
        if r['expected']:
            genuine.append(r['scores'][r['expected']])
            correct += prediction == r['expected']
            wrong += prediction is not None and prediction != r['expected']
            rejected += prediction is None
        else:
            unknown_correct += prediction is None
        impostor.extend(v for k, v in r['scores'].items()
                        if k != r['expected'])
    latencies = [r['latency'] for r in rows]
    return dict(
        attempts=len(rows), known_attempts=len(known),
        unknown_attempts=len(unknown),
        recognition_accuracy=correct / len(known) if known else None,
        unknown_rejection_accuracy=(unknown_correct / len(unknown)
                                    if unknown else None),
        wrong_identity_count=wrong, known_rejected=rejected,
        verification=verification_metrics(genuine, impostor, threshold),
        latency_median_ms=float(np.median(latencies)) if latencies else None,
        latency_p95_ms=float(np.percentile(latencies, 95))
        if latencies else None)


@app.get('/api/evaluation')
def evaluation():
    config = settings()
    rows = store.probes()
    return dict(
        settings=config,
        validation=evaluate(
            [r for r in rows if r['split'] == 'validation'],
            config['threshold'], config['margin']),
        test=evaluate(
            [r for r in rows if r['split'] == 'test'],
            config['threshold'], config['margin']))


@app.post('/api/calibrate')
def calibration():
    with lock:
        if settings()['calibrated']:
            raise ValueError(
                'Calibration is locked. Reset the experiment to recalibrate.')
        rows = [r for r in store.probes() if r['split'] == 'validation']
        known = [r for r in rows if r['expected']]
        unknown = [r for r in rows if not r['expected']]
        if len(known) < 5 or len(unknown) < 5:
            raise ValueError(
                'Collect at least 5 known and 5 unknown validation attempts; '
                'more are recommended.')
        genuine = [r['scores'][r['expected']] for r in known]
        impostor = [max(v for k, v in r['scores'].items()
                        if k != r['expected'])
                    for r in rows
                    if any(k != r['expected'] for k in r['scores'])]
        threshold = calibrate(genuine, impostor, 0.01)
        config = dict(threshold=threshold, margin=.08, calibrated=True,
                      created_at=now(), validation_attempts=len(rows),
                      target_far=.01)
        store.set_setting('calibration', config)
        stability.clear()
        return config


@app.delete('/api/evaluation')
def reset_evaluation():
    with lock:
        with store.connect() as db:
            store.invalidate(db)
        stability.clear()
    return {'ok': True}


@app.get('/api/evaluation.json')
def export_evaluation():
    report = evaluation()
    report.update(
        model='YuNet 2023mar + SFace 2021dec',
        matching='normalized centroid, cosine similarity',
        caveats=[
            'Local student experiment, not LFW',
            'Latency includes decode and detection, excludes network '
            'and frame confirmation',
            'Quality-rejected captures are not included; report capture '
            'failures separately',
            'Correlated attempts are not independent; use separate '
            'capture sessions',
            'No liveness detection; no population-wide accuracy claim'])
    return Response(json.dumps(report, indent=2), media_type='application/json',
                    headers={'Content-Disposition':
                             'attachment; filename="evaluation.json"'})


# ── Deep Learning Metrics Dashboard ───────────────────────────

from .lab import build_router
app.include_router(build_router(lambda: store, settings))


# ── Static frontend ───────────────────────────────────────────

dist = ROOT / 'frontend/dist'
if dist.exists():
    app.mount('/', StaticFiles(directory=dist, html=True), name='frontend')
