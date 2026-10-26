import {useState} from 'react';
import Camera from '../Camera';
import {api,percentage} from '../api';
import {useResource} from './useResource';

export default function ProbeEvaluation({state,refresh,confirm,onChange}) {
  const [expected,setExpected]=useState(''), [subject,setSubject]=useState('');
  const [batch,setBatch]=useState(''), [consent,setConsent]=useState(false);
  const [result,setResult]=useState(null), [error,setError]=useState(''), [busy,setBusy]=useState(false);
  const [revision,setRevision]=useState(0);
  const {data:report,error:reportError}=useResource('/evaluation',revision);
  const split=state.settings.calibrated?'test':'validation';
  const changed=()=>{setRevision(v=>v+1);onChange();};
  async function capture(image) {
    const data=await api('/probes',{method:'POST',body:{image,expected:expected||null,
      subject:expected||subject,batch,consent,split}});
    setResult(data);changed();
  }
  async function calibrate() {
    setBusy(true);setError('');
    try {await api('/calibrate',{method:'POST'}); await refresh();changed();}
    catch(e){setError(e.message);} finally{setBusy(false);}
  }
  return <details className="lab-panel lab-capture"><summary>Collect real evaluation attempts</summary>
    <p className="lab-muted">Calibration selects a recognition threshold. It does not train the neural network. Use separate capture sessions for enrollment, validation and test.</p>
    {(error||reportError)&&<div className="alert error" role="alert">{error||reportError}</div>}
    <div className="workspace">
      <Camera onFrame={capture} enabled={consent&&!!batch.trim()&&!!(expected||subject.trim())} result={result} actionLabel="Record labeled attempt"/>
      <section className="panel controls"><h2>{split==='test'?'Held-out test':'Validation captures'}</h2>
        <label>Expected identity<select value={expected} onChange={e=>setExpected(e.target.value)}><option value="">Unknown / not enrolled</option>{state.students.filter(s=>s.sample_count>0).map(s=><option key={s.id} value={s.id}>{s.name} · {s.roll_no}</option>)}</select></label>
        {!expected&&<label>Anonymous participant code<input value={subject} onChange={e=>setSubject(e.target.value)}/></label>}
        <label>Capture session / batch<input value={batch} onChange={e=>setBatch(e.target.value)} placeholder="day-2-evening"/></label>
        <label className="consent"><input type="checkbox" checked={consent} onChange={e=>setConsent(e.target.checked)}/><span>The participant explicitly consents to this evaluation.</span></label>
        <p className="lab-muted">Validation: {report?.validation.attempts??0} attempts. Test: {report?.test.attempts??0} attempts.</p>
        <button onClick={calibrate} disabled={busy||state.settings.calibrated}>{state.settings.calibrated?'Threshold locked':'Calibrate and lock threshold'}</button>
        <button className="text-button" onClick={()=>confirm({title:'Reset probe experiment?',description:'Deletes validation/test probes and calibration. Saved model runs remain.',run:async()=>{await api('/evaluation',{method:'DELETE'});await refresh();changed();}})}>Reset probe experiment</button>
      </section>
    </div>
    <section className="lab-probe-report" aria-label="Held-out recognition report">
      <div className="lab-run-heading"><h3>Held-out recognition report · all classes</h3><a className="button outline" href="/api/evaluation.json" download>Export probe report</a></div>
      <p className="lab-muted">Measured from independent test captures. Quality-rejected captures are excluded. These recognition results do not measure spoof detection.</p>
      <dl className="lab-metadata">
        {[
          ['Known-person recognition accuracy',percentage(report?.test.recognition_accuracy)],
          ['Unknown-person rejection accuracy',percentage(report?.test.unknown_rejection_accuracy)],
          ['Median recognition latency',report?.test.latency_median_ms==null?'—':`${report.test.latency_median_ms.toFixed(1)} ms`],
          ['95th percentile latency',report?.test.latency_p95_ms==null?'—':`${report.test.latency_p95_ms.toFixed(1)} ms`],
          ['Known test attempts',report?.test.known_attempts??'—'],
          ['Unknown test attempts',report?.test.unknown_attempts??'—'],
        ].map(([label,value])=><div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}
      </dl>
    </section>
  </details>;
}
