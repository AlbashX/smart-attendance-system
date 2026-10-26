"""Versioned experiment reports. Enrollment similarity is never training accuracy."""
import json
import uuid
from typing import Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator
from .store import now


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


class Epoch(StrictModel):
    epoch: int = Field(ge=1)
    train_accuracy: float = Field(ge=0, le=1)
    validation_accuracy: float = Field(ge=0, le=1)
    train_loss: float = Field(ge=0)
    validation_loss: float = Field(ge=0)


class ModelInfo(StrictModel):
    architecture: str = Field(min_length=1, max_length=150)
    embedding_size: int | None = Field(default=None, ge=1)
    optimizer: str | None = Field(default=None, max_length=80)
    learning_rate: float | None = Field(default=None, gt=0)
    batch_size: int | None = Field(default=None, ge=1)
    training_seconds: float | None = Field(default=None, ge=0)
    checkpoint: str | None = Field(default=None, max_length=200)
    dataset_version: str | None = Field(default=None, max_length=200)


class Counts(StrictModel):
    training_images: int | None = Field(default=None, ge=0)
    validation_images: int | None = Field(default=None, ge=0)


class Trial(StrictModel):
    # Positive means this student. Scores must use higher-is-more-similar convention.
    actual_positive: bool
    predicted_positive: bool
    similarity: float = Field(ge=-1, le=1)


class Run(StrictModel):
    class_id: str = Field(min_length=1, max_length=100)
    student_id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=120)
    model: ModelInfo
    counts: Counts = Field(default_factory=Counts)
    history: list[Epoch] = Field(default_factory=list, max_length=2000)
    trials: list[Trial] = Field(default_factory=list, max_length=10000)
    evaluation_split: Literal['test', 'validation'] = 'test'
    threshold: float = Field(default=.45, ge=-1, le=1)
    notes: str = Field(default='', max_length=2000)

    @model_validator(mode='after')
    def ordered_epochs(self):
        epochs = [e.epoch for e in self.history]
        if epochs != sorted(set(epochs)):
            raise ValueError('Epochs must be unique and increasing')
        return self


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def statistics(values):
    return {'count': len(values), 'mean': sum(values)/len(values) if values else None,
            'min': min(values) if values else None, 'max': max(values) if values else None}


def evaluate_trials(trials):
    tp = sum(t['actual_positive'] and t['predicted_positive'] for t in trials)
    fn = sum(t['actual_positive'] and not t['predicted_positive'] for t in trials)
    fp = sum(not t['actual_positive'] and t['predicted_positive'] for t in trials)
    tn = sum(not t['actual_positive'] and not t['predicted_positive'] for t in trials)
    precision, recall = ratio(tp,tp+fp), ratio(tp,tp+fn)
    scores = [t['similarity'] for t in trials]
    genuine = [t['similarity'] for t in trials if t['actual_positive']]
    impostor = [t['similarity'] for t in trials if not t['actual_positive']]
    roc, auc = [], None
    if genuine and impostor:
        # Tie-aware threshold sweep includes both endpoints. No fabricated AUC floor.
        roc = [{'fpr':0., 'tpr':0., 'threshold':None}]
        for cutoff in sorted(set(scores), reverse=True):
            roc.append({'threshold':cutoff, 'tpr':sum(s>=cutoff for s in genuine)/len(genuine),
                        'fpr':sum(s>=cutoff for s in impostor)/len(impostor)})
        auc = sum((b['fpr']-a['fpr'])*(b['tpr']+a['tpr'])/2 for a,b in zip(roc,roc[1:]))
    return dict(accuracy=ratio(tp+tn,len(trials)), precision=precision, recall=recall,
                f1=ratio(2*tp,2*tp+fp+fn), far=ratio(fp,fp+tn), frr=ratio(fn,fn+tp),
                confusion={'labels':['Other / unknown','Selected student'], 'matrix':[[tn,fp],[fn,tp]],
                           'tp':tp,'fp':fp,'fn':fn,'tn':tn}, attempts=len(trials),
                similarity=statistics(scores), distance=statistics([1-s for s in scores]),
                genuine=statistics(genuine), impostor=statistics(impostor), roc=roc, auc=auc)


def demo_run(class_id, student_id):
    history = [dict(epoch=i,train_accuracy=a,validation_accuracy=v,train_loss=l,validation_loss=w)
               for i,(a,v,l,w) in enumerate(zip([.55,.65,.74,.82,.87,.91,.94,.96],
                    [.53,.61,.70,.77,.82,.86,.88,.90],[1.1,.88,.7,.52,.4,.3,.23,.18],
                    [1.15,.96,.79,.63,.51,.42,.36,.33]),1)]
    scores = [.92,.88,.81,.77,.72,.68,.62,.31,.58,.56,.14,.21,.33,.37,.41,.53,.12,.24,.28,.34]
    return Run(class_id=class_id,student_id=student_id,name='Illustrative training run',
               model=ModelInfo(architecture='Example trainable recognition head + SFace',embedding_size=128,
                               optimizer='Adam (example)',learning_rate=.001,batch_size=16,training_seconds=84,
                               checkpoint='DEMO ONLY',dataset_version='synthetic-example'),
               counts=Counts(training_images=240,validation_images=60),history=history,
               trials=[Trial(actual_positive=i<10,predicted_positive=s>=.45,similarity=s) for i,s in enumerate(scores)],
               notes='Entire report is synthetic. Not evidence about this student or the deployed model.').model_dump()


def build_router(get_store, get_settings):
    router = APIRouter(prefix='/api/lab', tags=['Accuracy Lab'])

    def classes():
        groups = {}
        for r in get_store().timetable_rules():
            key = (r['course_name'], r.get('batch'))
            if key not in groups:
                groups[key] = dict(id=r['id'],name=r['course_name'],batch=r.get('batch'),rule_ids=[])
            groups[key]['rule_ids'].append(r['id'])
        return [dict(id='all',name='All classes',batch=None,rule_ids=None), *groups.values()]

    def scope(class_id, sid=None):
        cls = next((c for c in classes() if c['id']==class_id),None)
        if not cls:
            raise HTTPException(404,'Class not found')
        students = [s for s in get_store().students() if not cls['batch'] or s.get('batch')==cls['batch']]
        if sid is not None and not any(s['id']==sid for s in students):
            raise HTTPException(404,'Student does not belong to the selected class')
        return cls, students

    def attendance(cls, sid):
        with get_store().connect() as db:
            query = 'SELECT COUNT(*) FROM attendance a JOIN sessions s ON s.id=a.session_id WHERE a.student_id=?'
            params = [sid]
            if cls['rule_ids'] is not None:
                query += ' AND s.rule_id IN ('+','.join('?' for _ in cls['rule_ids'])+')'
                params += cls['rule_ids']
            return db.execute(query,params).fetchone()[0]

    @router.get('/classes')
    def list_classes():
        return classes()

    @router.get('/classes/{class_id}/students')
    def list_students(class_id: str):
        return [dict(id=s['id'],name=s['name'],roll_no=s['roll_no'],batch=s.get('batch'),
                     sample_count=s['sample_count']) for s in scope(class_id)[1]]

    @router.post('/runs', status_code=201)
    def save_run(body: Run):
        scope(body.class_id,body.student_id)
        rid = str(uuid.uuid4())
        with get_store().connect() as db:
            db.execute('INSERT INTO model_runs VALUES(?,?,?,?,?,?)',
                       (rid,body.class_id,body.student_id,body.name,now(),body.model_dump_json()))
        return {'id':rid,'source':'recorded'}

    @router.get('/classes/{class_id}/students/{sid}/runs')
    def list_runs(class_id: str, sid: str):
        scope(class_id,sid)
        with get_store().connect() as db:
            return [dict(r) for r in db.execute('SELECT id,name,created_at FROM model_runs WHERE class_id=? AND student_id=? ORDER BY created_at DESC',(class_id,sid))]

    def report(class_id, sid, run_id=None, source='real'):
        cls, students = scope(class_id,sid)
        student = next(s for s in students if s['id']==sid)
        created = None
        if source=='demo':
            data, provenance, rid = demo_run(class_id,sid),'demo','demo'
        else:
            with get_store().connect() as db:
                query = 'SELECT * FROM model_runs WHERE class_id=? AND student_id=?'
                params = [class_id,sid]
                if run_id:
                    query += ' AND id=?'
                    params.append(run_id)
                row = db.execute(query+' ORDER BY created_at DESC LIMIT 1',params).fetchone()
            if row:
                data,provenance,rid,created = json.loads(row['payload']),'recorded',row['id'],row['created_at']
            elif run_id:
                raise HTTPException(404,'Run not found in the selected class/student')
            else:
                cfg=get_settings()
                trials=[]
                for p in get_store().probes():
                    if p['split']!='test' or sid not in p['scores']:
                        continue
                    ranked=sorted(p['scores'].items(),key=lambda x:x[1],reverse=True)
                    best,score=ranked[0]
                    gap=score-ranked[1][1] if len(ranked)>1 else 2
                    trials.append(dict(actual_positive=p['expected']==sid,
                        predicted_positive=best==sid and score>=cfg['threshold'] and gap>=cfg['margin'],similarity=p['scores'][sid]))
                data=Run(class_id=class_id,student_id=sid,name='Current held-out recognition probes',
                    model=ModelInfo(architecture='YuNet + SFace (frozen pretrained)',embedding_size=128),
                    trials=trials,threshold=cfg['threshold'],
                    notes='Probe evaluation spans all classes because capture records have no class label. Enrollment is not model training.').model_dump()
                provenance,rid='local_probes','local-probes'
        history=data['history']
        return dict(id=rid,name=data['name'],source=provenance,created_at=created,
                    student={k:student.get(k) for k in ['id','name','roll_no','batch']},class_id=class_id,
                    history_scope='Model run (not a separate model trained for this student)',
                    evaluation_scope='Selected student versus other/unknown identities',
                    history=history,final=history[-1] if history else None,model=data['model'],
                    counts={**data['counts'],'enrollment_images':student['sample_count'],
                            'attendance_records':attendance(cls,sid)},
                    evaluation=evaluate_trials(data['trials']),threshold=data['threshold'],
                    evaluation_split=data['evaluation_split'],notes=data['notes'])

    @router.get('/classes/{class_id}/students/{sid}/metrics')
    def metrics(class_id: str,sid: str,run_id: str | None=None,source: Literal['real','demo']='real'):
        return report(class_id,sid,run_id,source)

    @router.get('/classes/{class_id}/summary')
    def summary(class_id: str):
        rows=[]
        for s in scope(class_id)[1]:
            r=report(class_id,s['id'])
            rows.append(dict(student_id=s['id'],name=s['name'],roll_no=s['roll_no'],source=r['source'],
                             run_name=r['name'],attempts=r['evaluation']['attempts'],
                             precision=r['evaluation']['precision'],recall=r['evaluation']['recall'],
                             f1=r['evaluation']['f1'],far=r['evaluation']['far'],frr=r['evaluation']['frr']))
        return rows

    return router
