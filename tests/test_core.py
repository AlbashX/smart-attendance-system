import numpy as np
import pytest
from backend.core import normalize, match, Stability, verification_metrics, calibrate
from backend.store import Store

def test_normalize_rejects_invalid():
    for v in ([0, 0], [float('nan'), 1], [float('inf'), 1]):
        with pytest.raises(ValueError): normalize(v)
    assert np.linalg.norm(normalize([3, 4])) == pytest.approx(1)

def test_unknown_and_ambiguous_are_not_identified():
    gallery = {'a': normalize([1, 0]), 'b': normalize([0, 1])}
    assert match(normalize([-1, 0]), gallery, .5, .08)['identity'] is None
    assert match(normalize([1, 1]), gallery, .5, .08)['identity'] is None
    assert match(normalize([1, 0]), gallery, .5, .08)['identity'] == 'a'

def test_stability_resets_after_unknown_and_long_gap():
    s = Stability()
    assert not s.observe('a', 1)
    assert not s.observe('a', 1.2)
    assert s.observe('a', 1.4)
    assert not s.observe(None, 1.5)
    assert not s.observe('a', 1.6)
    assert not s.observe('a', 10)

def test_metrics_have_correct_denominators():
    m = verification_metrics([.9, .2], [.6, .1], .5)
    assert m['far'] == .5 and m['frr'] == .5 and m['accuracy'] == .5
    t = calibrate([.8, .9], [.1, .2], 0)
    assert .2 < t <= .8

def test_attendance_unique_after_reopen_and_deletion(tmp_path):
    path = tmp_path / 'test.db'
    s = Store(path)
    p = s.add_student('T1', 'Test', email=None, section='D',
                      samples=[[1., 0.]], centroid=[1., 0.])
    session = s.start_session('Lab')
    assert s.mark(p, session, .8)
    assert not Store(path).mark(p, session, .9)
    assert len(s.records()) == 1
    s.delete_student(p)
    assert s.records() == []

def test_only_one_active_session(tmp_path):
    s = Store(tmp_path / 'test.db')
    s.start_session('First')
    with pytest.raises(ValueError): s.start_session('Second')
