import pytest
from fastapi.testclient import TestClient
from backend import main
from backend.store import Store
from backend.lab import evaluate_trials, demo_run


@pytest.fixture
def fixture(tmp_path,monkeypatch):
    db=Store(tmp_path/'test.db')
    monkeypatch.setattr(main,'store',db)
    sid=db.add_student('T1','Test Student',batch='D1')
    # add_student returns an ID, not a face enrollment.
    return TestClient(main.app),db,sid


def test_empty_has_no_invented_accuracy(fixture):
    client,db,sid=fixture
    r=client.get(f'/api/lab/classes/all/students/{sid}/metrics')
    assert r.status_code==200
    data=r.json()
    assert data['history']==[] and data['final'] is None
    assert data['evaluation']['accuracy'] is None
    assert data['evaluation']['far'] is None
    assert data['model']['optimizer'] is None
    assert data['counts']['training_images'] is None


def test_demo_is_explicit_and_not_saved(fixture):
    client,db,sid=fixture
    url=f'/api/lab/classes/all/students/{sid}'
    data=client.get(url+'/metrics?source=demo').json()
    assert data['source']=='demo' and len(data['history'])==8
    assert client.get(url+'/runs').json()==[]
    assert client.get(url+'/metrics').json()['history']==[]


def test_recorded_run_roundtrip_and_validation(fixture):
    client,db,sid=fixture
    body=demo_run('all',sid)
    # Synthetic values used only as a test fixture, never seeded into real storage.
    rid=client.post('/api/lab/runs',json=body).json()['id']
    report=client.get(f'/api/lab/classes/all/students/{sid}/metrics?run_id={rid}').json()
    assert report['source']=='recorded'
    assert report['evaluation']['confusion']['matrix']==[[9,1],[1,9]]
    assert report['evaluation']['f1']==.9
    assert report['final']['epoch']==8
    assert client.get(f'/api/lab/classes/all/students/{sid}/runs').json()[0]['id']==rid
    body['history'][1]['epoch']=1
    assert client.post('/api/lab/runs',json=body).status_code==422
    body['student_id']='missing'
    body['history']=[]
    assert client.post('/api/lab/runs',json=body).status_code==404


def test_real_probes_use_independent_trials(fixture):
    client,db,sid=fixture
    db.add_probe('test','known','test-A',sid,{sid:.9,'other':.1},12)
    db.add_probe('test','unknown','test-A',None,{sid:.7,'other':.1},12)
    data=client.get(f'/api/lab/classes/all/students/{sid}/metrics').json()
    assert data['evaluation']['attempts']==2
    assert data['evaluation']['far']==1
    assert data['evaluation']['precision']==.5
    assert data['history']==[]


def test_roc_can_be_worse_than_random():
    result=evaluate_trials([{'actual_positive':True,'predicted_positive':False,'similarity':.1},
                            {'actual_positive':False,'predicted_positive':True,'similarity':.9}])
    assert result['auc']==0
    assert result['roc'][0]['fpr']==0 and result['roc'][-1]['fpr']==1


def test_cross_origin_local_port_still_blocked(fixture):
    client,_,_=fixture
    assert client.post('/api/sessions',json={'name':'x'},headers={'Origin':'http://localhost:5173'}).status_code==403


def test_class_membership_and_saved_run_isolation(fixture):
    client,db,sid=fixture
    class_id=db.add_timetable_rule(0,'09:00','10:00','Lab',batch='D2')
    assert client.get(f'/api/lab/classes/{class_id}/students').json()==[]
    assert client.get(f'/api/lab/classes/{class_id}/students/{sid}/metrics').status_code==404
    assert client.post('/api/lab/runs',json=demo_run(class_id,sid)).status_code==404


def test_logger_saves_valid_history(tmp_path):
    from scripts.log_training_metrics import MetricsLogger
    import json
    logger=MetricsLogger('all','id','test',{'architecture':'Test CNN'},20,5)
    logger.log_epoch(1,.5,.4,1.2,1.3)
    logger.log_trial(True,False,.3)
    path=logger.save(tmp_path/'metrics.json',1.1)
    data=json.loads(path.read_text())
    assert data['history'][0]['validation_accuracy']==.4
    assert data['trials'][0]['predicted_positive'] is False
