import {useState} from 'react';
import {Activity,Download,RefreshCw,FlaskConical,Sun,Moon,Upload} from 'lucide-react';
import {api,percentage} from '../api';
import {useResource} from './useResource';
import MetricChart from './MetricChart';
import ProbeEvaluation from './ProbeEvaluation';
import './lab.css';

const number=(v,d=3)=>v==null?'—':Number(v).toFixed(d);
const value=v=>v==null?'Not recorded':v;
function Kpi({label,children,detail}){return <div className="lab-kpi"><span>{label}</span><strong>{children}</strong><small>{detail}</small></div>;}
function Empty({children}){return <div className="lab-empty"><Activity size={26}/><p>{children}</p></div>;}

export default function AccuracyLab({state,refresh,confirm}) {
  const [classId,setClass]=useState('all'),[studentId,setStudent]=useState(''),[runId,setRun]=useState('');
  const [source,setSource]=useState('real'),[revision,setRevision]=useState(0),[localError,setError]=useState('');
  const [theme,setTheme]=useState(()=>localStorage.getItem('lab-theme')||'light');
  const classes=useResource('/lab/classes',revision);
  const students=useResource(`/lab/classes/${encodeURIComponent(classId)}/students`,revision);
  const base=studentId?`/lab/classes/${encodeURIComponent(classId)}/students/${encodeURIComponent(studentId)}`:null;
  const runs=useResource(base?`${base}/runs`:null,revision);
  const selectedRun=(runs.data||[]).some(r=>r.id===runId)?runId:'';
  const report=useResource(base?`${base}/metrics?source=${source}${selectedRun?'&run_id='+encodeURIComponent(selectedRun):''}`:null,revision);
  const summary=useResource(`/lab/classes/${encodeURIComponent(classId)}/summary`,revision);
  const data=report.data, evaluation=data?.evaluation, final=data?.final;
  const history=data?.history||[];
  const refreshLab=()=>setRevision(v=>v+1);
  const error=localError||classes.error||students.error||runs.error||report.error||summary.error;
  const synthetic=data?.source==='demo';
  function chooseClass(id){setClass(id);setStudent('');setRun('');setError('');}
  function exportReport(){
    const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'});
    const link=document.createElement('a');link.href=URL.createObjectURL(blob);
    link.download=`${synthetic?'DEMO-':''}metrics-${data.id}.json`;link.click();URL.revokeObjectURL(link.href);
  }
  async function importRun(e){
    const file=e.target.files?.[0];if(!file)return;
    try{
      if(file.size>5_000_000)throw new Error('Metrics JSON must be under 5 MB.');
      const payload=JSON.parse(await file.text());
      if(payload.class_id!==classId||payload.student_id!==studentId)throw new Error('The file class_id and student_id must match your selection. See docs/accuracy-lab.md.');
      if(payload.source==='demo')throw new Error('Demo exports cannot be imported as real training results.');
      const saved=await api('/lab/runs',{method:'POST',body:payload});setSource('real');setRun(saved.id);setError('');refreshLab();
    }catch(e){setError(e.message);}finally{e.target.value='';}
  }
  return <div className="accuracy-dashboard" data-theme={theme}>
    <div className="lab-heading"><div><span className="lab-eyebrow">EXPERIMENT WORKSPACE</span><h2>Training and recognition metrics</h2><p>Inspect a saved run, evaluate a student, or explore a labeled example.</p></div>
      <div className="lab-actions"><button className="lab-icon" aria-label="Toggle dashboard theme" onClick={()=>{const next=theme==='light'?'dark':'light';setTheme(next);localStorage.setItem('lab-theme',next);}}>{theme==='light'?<Moon size={18}/>:<Sun size={18}/>}</button><button className="lab-icon" aria-label="Refresh metrics" onClick={refreshLab}><RefreshCw size={18}/></button></div>
    </div>
    <section className="lab-panel lab-filters" aria-label="Metrics selection">
      <label>Class<select value={classId} onChange={e=>chooseClass(e.target.value)} disabled={classes.loading}>{(classes.data||[{id:'all',name:'All classes'}]).map(c=><option key={c.id} value={c.id}>{c.name}{c.batch?` · ${c.batch}`:''}</option>)}</select></label>
      <label>Student<select value={studentId} onChange={e=>{setStudent(e.target.value);setRun('');setError('');}} disabled={students.loading}><option value="">{students.loading?'Loading students…':'Select a student'}</option>{(students.data||[]).map(s=><option key={s.id} value={s.id}>{s.name} · {s.roll_no}</option>)}</select></label>
      <label>Data source<select value={source} onChange={e=>{setSource(e.target.value);setRun('');}}><option value="real">Recorded results</option><option value="demo">Demo data (synthetic)</option></select></label>
      <label>Model run<select value={selectedRun} onChange={e=>setRun(e.target.value)} disabled={!studentId||source==='demo'||runs.loading}><option value="">{source==='demo'?'Illustrative run':runs.data?.length?'Latest saved run':'Current test probes'}</option>{(runs.data||[]).map(r=><option value={r.id} key={r.id}>{r.name} · {new Date(r.created_at).toLocaleString()}</option>)}</select></label>
    </section>
    {error&&<div className="alert error" role="alert">{error}<button className="text-button" onClick={()=>{setError('');refreshLab();}}>Retry</button></div>}
    {report.loading&&<div className="lab-panel" role="status">Loading metrics…</div>}
    {!studentId&&<section className="lab-panel"><Empty>Select a student to load measured results. Choose Demo data to preview all charts with synthetic examples.</Empty></section>}
    {data&&<>
      <div className={`lab-provenance ${synthetic?'demo':''}`} role="status"><FlaskConical size={19}/><div><b>{synthetic?'DEMO DATA — NOT MEASURED RESULTS':data.source==='recorded'?'Saved experiment report':'Live view of recorded test probes'}</b><p>{synthetic?'Charts and model values are illustrative; attendance and enrollment counts below remain live.':data.notes}</p></div></div>
      <div className="lab-run-heading"><div><h3>{data.student.name} <span className="lab-muted">{data.student.roll_no}</span></h3><p className="lab-muted">{data.name} · {data.evaluation_split} evaluation{data.created_at?` · ${new Date(data.created_at).toLocaleString()}`:''}</p></div><div className="lab-actions"><button className="outline" onClick={exportReport}><Download size={15}/>Export report</button><label className="button outline lab-import"><Upload size={15}/>Import run<input type="file" accept="application/json,.json" onChange={importRun}/></label></div></div>
      <section className="lab-kpis" aria-label="Training summary">
        <Kpi label="Training accuracy" detail="Final logged epoch">{percentage(final?.train_accuracy)}</Kpi><Kpi label="Validation accuracy" detail="Final logged epoch">{percentage(final?.validation_accuracy)}</Kpi>
        <Kpi label="Training loss" detail="Final logged epoch">{number(final?.train_loss,4)}</Kpi><Kpi label="Validation loss" detail="Final logged epoch">{number(final?.validation_loss,4)}</Kpi>
      </section>
      <p className="lab-muted lab-scope">{data.history_scope}. Blank values mean no training history was logged.</p>
      <section className="lab-grid">
        <div className="lab-panel"><h3>Accuracy over epochs</h3>{history.length?<MetricChart title="Accuracy" theme={theme} unitInterval labels={history.map(e=>e.epoch)} series={[{name:'Training',color:'#11a79f',values:history.map(e=>e.train_accuracy)},{name:'Validation',color:'#8b7cf6',values:history.map(e=>e.validation_accuracy)}]}/>:<Empty>No epoch accuracy recorded. Import a training run.</Empty>}</div>
        <div className="lab-panel"><h3>Loss over epochs</h3>{history.length?<MetricChart title="Loss" theme={theme} labels={history.map(e=>e.epoch)} series={[{name:'Training',color:'#11a79f',values:history.map(e=>e.train_loss)},{name:'Validation',color:'#e69a4c',values:history.map(e=>e.validation_loss)}]}/>:<Empty>No training loss recorded for frozen pretrained inference.</Empty>}</div>
      </section>
      <section className="lab-kpis lab-six" aria-label="Evaluation metrics">
        {[['Test / evaluation accuracy',evaluation.accuracy],['Precision',evaluation.precision],['Recall',evaluation.recall],['F1-score',evaluation.f1],['False acceptance',evaluation.far],['False rejection',evaluation.frr]].map(([label,v])=><Kpi key={label} label={label} detail={`${evaluation.attempts} labeled attempts`}>{percentage(v)}</Kpi>)}
      </section>
      <section className="lab-grid">
        <div className="lab-panel"><h3>Confusion matrix</h3><p className="lab-muted">Rows: actual identity. Columns: predicted identity.</p>{evaluation.attempts?<div className="lab-heatmap-wrap"><table className="lab-heatmap"><thead><tr><th>Actual / predicted</th>{evaluation.confusion.labels.map(s=><th key={s}>{s}</th>)}</tr></thead><tbody>{evaluation.confusion.matrix.map((row,i)=><tr key={i}><th>{evaluation.confusion.labels[i]}</th>{row.map((v,j)=><td key={j} style={{background:`rgba(8,127,131,${.1+.75*v/Math.max(1,...evaluation.confusion.matrix.flat())})`}}><b>{v}</b><span>{[['TN','FP'],['FN','TP']][i][j]}</span></td>)}</tr>)}</tbody></table></div>:<Empty>No labeled evaluation attempts.</Empty>}<p className="lab-muted">Positive class: selected student. FAR = FP / (FP + TN). FRR = FN / (FN + TP).</p></div>
        <div className="lab-panel"><h3>ROC curve <span className="lab-muted">AUC {number(evaluation.auc)}</span></h3>{evaluation.roc.length?<MetricChart title="ROC curve" theme={theme} roc series={[{name:'Similarity threshold',color:'#11a79f',values:evaluation.roc.map(p=>({x:p.fpr,y:p.tpr}))},{name:'Chance',color:'#94a3b8',values:[{x:0,y:0},{x:1,y:1}]}]}/>:<Empty>ROC needs both genuine and impostor attempts.</Empty>}<p className="lab-muted">Threshold sweep uses similarity only. Runtime decisions may also apply an ambiguity margin.</p></div>
      </section>
      <section className="lab-grid">
        <div className="lab-panel"><h3>Match score statistics</h3><p className="lab-muted">Cosine similarity is a score, not a probability. Distance = 1 − similarity.</p><div className="lab-table-wrap"><table><thead><tr><th>Scores</th><th>Count</th><th>Mean</th><th>Min</th><th>Max</th></tr></thead><tbody>{[['Similarity',evaluation.similarity],['Distance',evaluation.distance],['Genuine',evaluation.genuine],['Impostor',evaluation.impostor]].map(([label,s])=><tr key={label}><th>{label}</th><td>{s.count}</td><td>{number(s.mean)}</td><td>{number(s.min)}</td><td>{number(s.max)}</td></tr>)}</tbody></table></div></div>
        <div className="lab-panel"><h3>Dataset and attendance</h3><dl className="lab-facts">{[['Training images (run)',data.counts.training_images],['Validation images (run)',data.counts.validation_images],['Enrollment images (live)',data.counts.enrollment_images],['Attendance records (selected class)',data.counts.attendance_records],['Evaluation attempts',evaluation.attempts]].map(([label,v])=><div key={label}><dt>{label}</dt><dd>{value(v)}</dd></div>)}</dl><p className="lab-muted">Enrollment counts are not training counts. Attendance records include present and absent entries.</p></div>
      </section>
      <section className="lab-panel"><h3>Model metadata</h3><dl className="lab-metadata">{[['Architecture',data.model.architecture],['Embedding size',data.model.embedding_size],['Optimizer',data.model.optimizer],['Learning rate',data.model.learning_rate],['Batch size',data.model.batch_size],['Logged epochs',history.length||null],['Training time (seconds)',data.model.training_seconds],['Checkpoint',data.model.checkpoint],['Dataset version',data.model.dataset_version],['Decision threshold',data.threshold]].map(([label,v])=><div key={label}><dt>{label}</dt><dd>{value(v)}</dd></div>)}</dl></section>
      {history.length>0&&<details className="lab-panel"><summary>Per-epoch values</summary><div className="lab-table-wrap"><table><thead><tr><th>Epoch</th><th>Train accuracy</th><th>Validation accuracy</th><th>Train loss</th><th>Validation loss</th></tr></thead><tbody>{history.map(e=><tr key={e.epoch}><td>{e.epoch}</td><td>{percentage(e.train_accuracy)}</td><td>{percentage(e.validation_accuracy)}</td><td>{number(e.train_loss,4)}</td><td>{number(e.validation_loss,4)}</td></tr>)}</tbody></table></div></details>}
    </>}
    <details className="lab-panel"><summary>Detailed metrics for the selected class</summary><p className="lab-muted">Real results only. Each student uses their latest saved run or current test probes; runs may differ. No pooled class accuracy is implied.</p><div className="lab-table-wrap"><table><thead><tr><th>Student</th><th>Run / source</th><th>Attempts</th><th>Precision</th><th>Recall</th><th>F1</th><th>FAR</th><th>FRR</th></tr></thead><tbody>{(summary.data||[]).map(r=><tr key={r.student_id}><td>{r.name}<small> {r.roll_no}</small></td><td>{r.source==='recorded'?r.run_name:'Current test probes'}</td><td>{r.attempts}</td>{['precision','recall','f1','far','frr'].map(k=><td key={k}>{percentage(r[k])}</td>)}</tr>)}</tbody></table>{summary.loading&&<p role="status">Loading class results…</p>}{!summary.loading&&!summary.data?.length&&<Empty>No students in this class.</Empty>}</div></details>
    <ProbeEvaluation state={state} refresh={refresh} confirm={confirm} onChange={refreshLab}/>
  </div>;
}
