import React, { useEffect, useState, useRef } from 'react';
import { createRoot } from 'react-dom/client';
import { ScanFace, Video, Users, ClipboardList, FlaskConical, ShieldCheck, UserPlus, Clock3, UserCheck, Play, Download, Search, Trash2, ArrowLeft, Check, Info, X, ChevronRight, LockKeyhole, RotateCcw, Calendar, Upload, Camera as CameraIcon, FileVideo, AlertTriangle, Pencil, Plus, BookOpen, GraduationCap, Cpu, Activity, Sparkles, Layers } from 'lucide-react';
import Camera from './Camera';
import Lab from './lab/AccuracyLab';
import { api, uploadFile, percentage, timeLabel } from './api';
import './styles.css';

const DAY_NAMES = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
const NAV = [
  {id:'live',name:'Live attendance',icon:Video},
  {id:'schedule',name:'Schedule',icon:Calendar},
  {id:'students',name:'Students',icon:Users},
  {id:'records',name:'Attendance records',icon:ClipboardList},
  {id:'lab',name:'Accuracy lab',icon:FlaskConical},
];
const TITLES = {
  live:['Live attendance','Monitor and recognize enrolled students in real time.'],
  schedule:['Class schedule','Weekly timetable with editing and exception management.'],
  students:['Students','Enrolled student roster with consent-based face enrollment.'],
  records:['Attendance records','View attendance by date and class session.'],
  lab:['Accuracy lab','Calibrate on validation data. Measure on a separate test set.'],
  enroll:['Enroll student','Capture varied, clear face samples of one consenting student.'],
};

function Empty({icon:Icon=ClipboardList,children}) {
  return <div className="empty"><Icon size={26} strokeWidth={1.5}/><p>{children}</p></div>;
}

function Metric({icon:Icon,label,value,detail}) {
  return <div className="metric"><Icon size={23} strokeWidth={1.6}/><div><span>{label}</span><strong>{value}</strong>{detail && <small>{detail}</small>}</div></div>;
}

function StatusBadge({status}) {
  return <span className={`status-badge ${status}`}>{status === 'present' ? 'Present' : 'Absent'}</span>;
}

function App() {
  const [page,setPage] = useState('live');
  const [state,setState] = useState(null);
  const [error,setError] = useState('');
  const [toast,setToast] = useState('');
  const [confirmation,setConfirmation] = useState(null);
  const [busy,setBusy] = useState(false);

  async function refresh() { const data = await api('/state'); setState(data); }
  useEffect(() => { refresh().catch(e => setError(e.message)); }, []);
  useEffect(() => { if (!toast) return; const id = setTimeout(() => setToast(''), 4000); return () => clearTimeout(id); }, [toast]);

  async function action(fn, message) {
    setError('');
    try { await fn(); await refresh(); if (message) setToast(message); }
    catch (e) { setError(e.message); }
  }
  async function confirmAction() {
    setBusy(true);
    try { await confirmation.run(); await refresh(); setConfirmation(null); setToast('Changes saved.'); }
    catch (e) { setError(e.message); setConfirmation(null); }
    finally { setBusy(false); }
  }
  const nav = id => { setPage(id); setError(''); };

  return <div className="app-shell">
    <aside className="sidebar">
      <a className="brand" href="#" onClick={e => {e.preventDefault(); nav('live');}}>
        <ScanFace size={34} strokeWidth={1.7}/>
        <div><strong>Attend</strong><span>Classroom attendance</span></div>
      </a>
      <nav aria-label="Main navigation">
        {NAV.map(({id,name,icon:Icon}) =>
          <button key={id} aria-label={name} title={name}
            className={page === id || (page === 'enroll' && id === 'students') ? 'nav-item selected' : 'nav-item'}
            onClick={() => nav(id)} aria-current={page === id ? 'page' : undefined}>
            <Icon size={21}/><span>{name}</span>
          </button>
        )}
      </nav>
      <div className="sidebar-footer"><ShieldCheck size={19}/><span>Local processing</span><i/></div>
    </aside>

    <main>
      <header>
        <div>
          <h1>{TITLES[page]?.[0]}</h1>
          <p>{TITLES[page]?.[1]}</p>
        </div>
        {page !== 'enroll' && page !== 'schedule' &&
          <button className="outline" onClick={() => nav('enroll')}><UserPlus size={18}/>Enroll student</button>
        }
      </header>

      {error && <div className="alert error" role="alert"><Info size={18}/><span>{error}</span><button className="icon-button" aria-label="Dismiss error" onClick={() => setError('')}><X size={17}/></button></div>}

      {!state ?
        <div className="panel"><Empty>Connecting to the local recognition service…</Empty><button onClick={() => action(refresh)}>Retry connection</button></div>
      : <>
        {!state.models_ready && <div className="alert error">Models are missing. Run the model download script before using the camera.</div>}
        {page === 'live' && <Live state={state} refresh={refresh} action={action}/>}
        {page === 'schedule' && <Schedule state={state} refresh={refresh} action={action} setToast={setToast} setError={setError}/>}
        {page === 'students' && <Students state={state} enroll={() => nav('enroll')} confirm={setConfirmation} refresh={refresh} setToast={setToast} setError={setError}/>}
        {page === 'enroll' && <Enrollment state={state} onDone={async () => { await refresh(); nav('students'); setToast('Student enrolled.'); }} back={() => nav('students')} setError={setError}/>}
        {page === 'records' && <Records state={state}/>}
        {page === 'lab' && <Lab state={state} refresh={refresh} confirm={setConfirmation}/>}
      </>}

      <footer/>
    </main>

    {toast && <div className="toast" role="status"><Check size={18}/>{toast}</div>}
    {confirmation && <div className="modal-backdrop">
      <section className="modal" role="alertdialog" aria-modal="true" aria-labelledby="confirm-title">
        <h2 id="confirm-title">{confirmation.title}</h2>
        <p>{confirmation.description}</p>
        <div className="button-row">
          <button autoFocus className="outline" disabled={busy} onClick={() => setConfirmation(null)}>Cancel</button>
          <button className="danger" disabled={busy} onClick={confirmAction}>{busy ? 'Working…' : 'Confirm'}</button>
        </div>
      </section>
    </div>}
  </div>;
}


/* ── Live Attendance ─────────────────────────────────────────── */

function Live({state,refresh,action}) {
  const [result,setResult] = useState(null);
  const [pending,setPending] = useState(false);
  const [streamId] = useState(() => {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  // Fallback UUID v4 generator for non-secure contexts
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
});

  const session = state.active_session;
  const currentClasses = state.current_classes || (state.current_class ? [state.current_class] : []);
  const nextClass = state.next_class;

  const [selectedRuleId, setSelectedRuleId] = useState(() => currentClasses[0]?.id || '');
  const todayClasses = (state.timetable || []).filter(r => r.weekday === state.weekday);
  const [selectedAdHocId, setSelectedAdHocId] = useState(() => todayClasses[0]?.id || '');

  // Keep selection valid when classes change
  useEffect(() => {
    if (currentClasses.length > 0 && !currentClasses.some(c => c.id === selectedRuleId)) {
      setSelectedRuleId(currentClasses[0].id);
    }
  }, [currentClasses, selectedRuleId]);

  const selectedClass = currentClasses.find(c => c.id === selectedRuleId) || currentClasses[0] || null;
  const activeRule = (session?.rule_id && state.timetable.find(r => r.id === session.rule_id)) || state.current_class;
  const selectedAdHoc = todayClasses.find(c => c.id === selectedAdHocId) || todayClasses[0] || null;

  const dlMetrics = state.dl_metrics;
  const currentBatch = selectedClass?.batch || activeRule?.batch || null;
  const batchStudents = state.students.filter(s => currentBatch ? s.batch === currentBatch : true);
  const batchEnrolledCount = batchStudents.filter(s => s.sample_count > 0).length;

  // Fetch session records
  const [records, setRecords] = useState([]);
  useEffect(() => {
    if (session) {
      api(`/attendance?session_id=${session.id}`).then(setRecords).catch(() => {});
    } else {
      setRecords([]);
    }
  }, [session?.id, result?.marked]);

  // Aggregate latest attendance records per student
  const studentRecords = new Map();
  for (const r of (records.length ? records : state.records || [])) {
    if (!studentRecords.has(r.student_id) || r.status === 'present') {
      studentRecords.set(r.student_id, r);
    }
  }

  const batchPresentCount = batchStudents.filter(s => studentRecords.get(s.id)?.status === 'present').length;

  async function recognize(image) {
    const r = await api('/recognize', {method:'POST', body:{image, stream_id:streamId, session_id:session?.id || null}});
    setResult(r);
    if (r.marked) await refresh();
  }

  async function startSession(classToStart = selectedClass) {
    if (!classToStart) return;
    setPending(true);
    await action(() => api('/sessions', {method:'POST', body:{
      name: `${classToStart.course_name}${classToStart.batch ? ` (${classToStart.batch})` : ''}`,
      rule_id: classToStart.id,
      date: state.today
    }}), 'Session started.');
    setPending(false);
    setResult(null);
  }

  async function endSession() {
    if (!session) return;
    setPending(true);
    await action(() => api(`/sessions/${session.id}/end`, {method:'POST'}), 'Session ended. Absent students marked.');
    setPending(false);
    setResult(null);
  }

  return <>
    {/* Current class info banner */}
    <div className="current-class-banner">
      {session ? <>
        <div className="class-info">
          <span className="live-dot"/><strong>{session.name}</strong>
          {activeRule && <span className="class-detail">{activeRule.teacher} · {activeRule.start_time}–{activeRule.end_time} · {activeRule.room || 'Room TBD'}{activeRule.batch ? ` · Batch ${activeRule.batch}` : ' · Section D'}</span>}
        </div>
        <button className="outline danger-outline" disabled={pending} onClick={endSession}><X size={15}/>{pending ? 'Ending…' : 'End session'}</button>
      </> : currentClasses.length > 0 ? <>
        <div className="class-info multi-class-info">
          <div className="class-header-row">
            <Calendar size={18}/>
            {currentClasses.length > 1 ? (
              <span className="multi-label">Select ongoing lab / class:</span>
            ) : (
              <strong>{selectedClass?.course_name}</strong>
            )}
          </div>
          {currentClasses.length > 1 && (
            <div className="class-picker-pills" role="radiogroup" aria-label="Select ongoing lab or class">
              {currentClasses.map(c => (
                <button
                  key={c.id}
                  type="button"
                  className={`class-pill ${selectedClass?.id === c.id ? 'active' : ''}`}
                  onClick={() => setSelectedRuleId(c.id)}
                  aria-checked={selectedClass?.id === c.id}
                  role="radio"
                >
                  <BookOpen size={14}/>
                  <span>{c.course_name}</span>
                  {c.batch && <span className="pill-batch">{c.batch}</span>}
                </button>
              ))}
            </div>
          )}
          {selectedClass && (
            <span className="class-detail">
              {selectedClass.teacher} · {selectedClass.start_time}–{selectedClass.end_time} · {selectedClass.room || 'Room TBD'}{selectedClass.batch ? ` · Batch ${selectedClass.batch}` : ' · Section D'}
            </span>
          )}
        </div>
        <button disabled={pending || !selectedClass} onClick={() => startSession(selectedClass)}>
          <Play size={15}/>{pending ? 'Starting…' : `Start session${selectedClass?.batch ? ` (${selectedClass.batch})` : ''}`}
        </button>
      </> : <>
        <div className="class-info multi-class-info">
          <div className="class-header-row">
            <Clock3 size={18}/>
            <strong>No scheduled class right now</strong>
            {nextClass && <span className="class-detail">Next: {nextClass.course_name} · {nextClass.start_time}–{nextClass.end_time}</span>}
            {!nextClass && <span className="class-detail">No more classes today ({state.day_name})</span>}
          </div>
          {todayClasses.length > 0 && (
            <div className="adhoc-session-picker">
              <span className="small-muted">Or select any session from today's schedule:</span>
              <div className="class-picker-pills">
                {todayClasses.map(c => (
                  <button
                    key={c.id}
                    type="button"
                    className={`class-pill ${selectedAdHoc?.id === c.id ? 'active' : ''}`}
                    onClick={() => setSelectedAdHocId(c.id)}
                  >
                    <BookOpen size={13}/>
                    <span>{c.course_name}</span>
                    {c.batch && <span className="pill-batch">{c.batch}</span>}
                    <small className="pill-time">{c.start_time}</small>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
        {selectedAdHoc && (
          <button disabled={pending} onClick={() => startSession(selectedAdHoc)}>
            <Play size={15}/>{pending ? 'Starting…' : `Start ${selectedAdHoc.batch ? `(${selectedAdHoc.batch})` : 'session'}`}
          </button>
        )}
      </>}
    </div>

    {/* Deep Learning Metrics Cards */}
    <div className="metrics metrics-4">
      <Metric
        icon={GraduationCap}
        label={`${currentBatch ? `Batch ${currentBatch}` : 'Class'} Enrolled`}
        value={`${batchEnrolledCount} / ${batchStudents.length}`}
        detail={`${percentage(batchStudents.length ? batchEnrolledCount / batchStudents.length : 0)} gallery coverage`}
      />
      <Metric
        icon={ShieldCheck}
        label="Gallery separation"
        value={dlMetrics?.gallery_separation_rate != null ? percentage(dlMetrics.gallery_separation_rate) : '—'}
        detail="Centroid separation only; not test accuracy"
      />
      <Metric
        icon={FlaskConical}
        label="Max Impostor Sim"
        value={dlMetrics?.max_impostor_similarity != null ? dlMetrics.max_impostor_similarity.toFixed(3) : '—'}
        detail={`Boundary τ = ${state.settings.threshold.toFixed(2)} (+${(dlMetrics?.max_impostor_similarity == null ? '—' : (state.settings.threshold - dlMetrics.max_impostor_similarity).toFixed(3))} gap)`}
      />
      <Metric
        icon={Clock3}
        label="Inference Latency"
        value={result?.latency_ms ? `${result.latency_ms} ms` : '—'}
        detail="YuNet ONNX + SFace 128-d"
      />
    </div>

    {/* Deep Learning Architecture & Telemetry Strip */}
    <div className="dl-telemetry-bar">
      <div className="dl-chip">
        <span className="dl-chip-label">Face Detector</span>
        <b>YuNet 2023mar</b>
        <span className="chip-sub">ONNX · 640×480 · 5 Landmarks</span>
      </div>
      <div className="dl-chip">
        <span className="dl-chip-label">Feature Embedder</span>
        <b>SFace 2021dec</b>
        <span className="chip-sub">128-d L2 Normalized Centroids</span>
      </div>
      <div className="dl-chip">
        <span className="dl-chip-label">Similarity Metric</span>
        <b>Cosine Similarity</b>
        <span className="chip-sub">u · v ∈ [-1.0, +1.0]</span>
      </div>
      <div className="dl-chip">
        <span className="dl-chip-label">Decision Boundary</span>
        <b>τ ≥ {state.settings.threshold.toFixed(2)} · Δ ≥ {state.settings.margin.toFixed(2)}</b>
        <span className="chip-sub">{state.settings.calibrated ? 'Validation Calibrated' : 'Provisional Baseline'}</span>
      </div>
      <div className="dl-chip">
        <span className="dl-chip-label">Temporal Voting</span>
        <b>3-Frame Queue</b>
        <span className="chip-sub">Anti-spoof jitter filter</span>
      </div>
    </div>

    <div className="workspace">
      <Camera key={session?.id || 'preview'} onFrame={recognize} automatic enabled={state.models_ready} result={result}/>
      <section className="panel controls">
        <div className="panel-heading" style={{marginBottom:10}}>
          <h2>Recognition status</h2>
          <span className="tech-tag"><Cpu size={12}/> DL Live</span>
        </div>
        <div className="divider" style={{margin:'14px 0'}}/>
        <h3>Deep Learning Verification Pipeline</h3>
        {[
          ['Single face detection', result?.face_count ? `1 face found [${result.box?.slice(0, 2).join(',')}]` : 'Awaiting subject', result?.face_count === 1],
          ['Quality & illumination', result?.quality ? 'Illumination & blur checks passed' : 'Illumination / sharpness gate', result?.quality],
          ['3-Frame temporal stability', result?.stable ? 'Confidence confirmed across 3 frames' : `${result?.stable_count || 0}/3 consecutive matching frames`, result?.stable],
        ].map(([title,description,passed]) =>
          <div className="check-row" key={title}>
            <span className={`check-dot ${passed ? 'passed' : ''}`}>{passed && <Check size={12}/>}</span>
            <div><b>{title}</b><small>{description}</small></div>
          </div>
        )}

        <div className="temporal-gate">
          <span className="temporal-label">Temporal Queue:</span>
          <div className="temporal-dots">
            <span className={`temp-dot ${result?.stable_count >= 1 ? 'active' : ''}`}/>
            <span className={`temp-dot ${result?.stable_count >= 2 ? 'active' : ''}`}/>
            <span className={`temp-dot ${result?.stable ? 'active confirmed' : ''}`}/>
          </div>
          <span className="temporal-text">{result?.stable ? '3/3 Confirmed' : `${result?.stable_count || 0}/3 frames`}</span>
        </div>

        {result?.score != null && (
          <div style={{background:'#f6f9fb',padding:10,borderRadius:6,margin:'12px 0'}}>
            <div className="dl-inspector-row"><span>Cosine Similarity:</span><b>{result.score.toFixed(4)}</b></div>
            <div className="dl-inspector-row"><span>Boundary Threshold:</span><b>τ = {state.settings.threshold.toFixed(2)}</b></div>
            <div className="dl-inspector-row"><span>Ambiguity Separation:</span><b>Δ = +{(result.gap || 0).toFixed(3)}</b></div>
            <div className="dl-inspector-row"><span>Vector Dimension:</span><b>128-d Unit Norm</b></div>
            <div className="dl-inspector-row"><span>Pipeline Latency:</span><b>{result.latency_ms} ms</b></div>
          </div>
        )}

        {result?.name && <div className="match-result">
          <UserCheck size={18}/>
          <div>
            <b>{result.name}</b> <small className="muted">({result.roll_no})</small>
            <small>{result.stable ? (session ? 'Verified match · attendance recorded' : 'Verified match · start session to record') : 'Confirming identity in temporal queue…'}</small>
          </div>
        </div>}
        {result?.identity === null && result?.reason === 'Unknown' && result?.quality &&
          <div className="unknown-result">
            <AlertTriangle size={18}/>
            <div><b>Unknown / Unenrolled person</b><small>Cosine score is below threshold ({state.settings.threshold.toFixed(2)}).</small></div>
          </div>
        }
        {result?.reason === 'Ambiguous match' &&
          <div className="unknown-result" style={{borderColor:'#e5ad38',background:'#fdfaf2'}}>
            <AlertTriangle size={18} color="#b37c09"/>
            <div><b>Ambiguous separation</b><small>Top-1 and Top-2 score separation &lt; {state.settings.margin.toFixed(2)} margin.</small></div>
          </div>
        }
        <p className="caption"><Info size={16}/> Unknown faces are never marked present. One verified sighting (3-frame confirmation) marks attendance.</p>
      </section>
    </div>

    <div className={`calibration-note ${state.settings.calibrated ? 'calibrated' : ''}`}>
      <FlaskConical size={17}/>
      <span>{state.settings.calibrated ? 'Validation-calibrated threshold' : 'Uncalibrated starting threshold'}: {state.settings.threshold.toFixed(3)} · {state.settings.calibrated ? 'Evaluate the held-out test set before reporting accuracy.' : 'Use Accuracy lab to tune this for your student group.'}</span>
    </div>

    {/* Selected Class Student Deep Learning & Validation Roster */}
    <section className="panel dl-students-section">
      <div className="panel-heading">
        <div>
          <div className="dl-badge-title">
            <h2>{selectedClass?.course_name || 'Class'} {currentBatch ? `(Batch ${currentBatch})` : ''} — Student Validation & Biometrics Roster</h2>
            <span className="tech-tag"><Activity size={12}/> Deep Learning Roster</span>
          </div>
          <p className="muted small">
            Student biometrics, 128-d centroid embeddings, pairwise validation safety margins, and live attendance for {selectedClass?.teacher} ({selectedClass?.room || 'Room TBD'} · {selectedClass?.start_time}–{selectedClass?.end_time}).
          </p>
        </div>
        <div className="roster-filters">
          <span className="filter-stat"><b>{batchEnrolledCount}</b> / {batchStudents.length} enrolled</span>
          <span className="filter-stat present-stat"><b>{batchPresentCount}</b> present</span>
          <span className="filter-stat"><b>{dlMetrics?.gallery_separation_rate != null ? percentage(dlMetrics.gallery_separation_rate) : '—'}</b> gallery separation</span>
        </div>
      </div>

      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Student</th>
              <th>Roll No</th>
              <th>Batch</th>
              <th>Biometric Embedding (DL)</th>
              <th>Validation Margin to Impostor</th>
              <th>Cosine Similarity Score</th>
              <th>Attendance Status</th>
            </tr>
          </thead>
          <tbody>
            {batchStudents.map(s => {
              const studentMetric = dlMetrics?.student_metrics?.[s.id];
              const rec = studentRecords.get(s.id);
              const isPresent = rec?.status === 'present';
              const isAbsent = rec?.status === 'absent';
              const isEnrolled = s.sample_count > 0;
              const maxImp = studentMetric?.max_impostor;
              const marginGap = studentMetric?.margin_to_threshold;
              const latestSim = isPresent && rec?.similarity != null ? rec.similarity : null;

              return (
                <tr key={s.id}>
                  <td>
                    <span className="avatar">{s.name?.[0]?.toUpperCase()}</span>
                    <b>{s.name}</b>
                    {s.email && <small className="muted" style={{display:'block'}}>{s.email}</small>}
                  </td>
                  <td><b>{s.roll_no}</b></td>
                  <td><span className="batch-tag">{s.batch || 'Section D'}</span></td>
                  <td>
                    {isEnrolled ? (
                      <span className="vector-badge active">
                        <Check size={13}/> 128-d Centroid ({s.sample_count}/5 samples)
                      </span>
                    ) : (
                      <span className="vector-badge">
                        No biometric data
                      </span>
                    )}
                  </td>
                  <td>
                    {isEnrolled && maxImp != null ? (
                      <div className="sim-score-cell">
                        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
                          <span className="margin-pill safe">
                            Max Imp: {maxImp.toFixed(3)}
                          </span>
                          <small className="muted">Gap: +{marginGap > 0 ? marginGap.toFixed(3) : '0.000'}</small>
                        </div>
                        <div className="sim-score-bar" title={`Max impostor similarity ${maxImp.toFixed(3)} vs threshold ${state.settings.threshold.toFixed(2)}`}>
                          <div
                            className={`sim-score-fill ${maxImp < state.settings.threshold ? 'high' : 'margin'}`}
                            style={{width: `${Math.min(100, Math.max(10, maxImp * 100))}%`}}
                          />
                        </div>
                      </div>
                    ) : (
                      <span className="muted">—</span>
                    )}
                  </td>
                  <td>
                    {latestSim != null ? (
                      <div className="sim-score-cell">
                        <span className="score" style={{background:'#e3f6ef',color:'#0a7e63',fontWeight:700}}>
                          {latestSim.toFixed(3)} ({percentage(latestSim)})
                        </span>
                        <div className="sim-score-bar">
                          <div className="sim-score-fill high" style={{width: `${Math.min(100, latestSim * 100)}%`}}/>
                        </div>
                      </div>
                    ) : isEnrolled ? (
                      <span className="score" style={{background:'#f1f5f9',color:'#475569'}}>
                        Template ready (τ ≥ {state.settings.threshold.toFixed(2)})
                      </span>
                    ) : (
                      <span className="muted">—</span>
                    )}
                  </td>
                  <td>
                    {isPresent ? (
                      <StatusBadge status="present"/>
                    ) : isAbsent ? (
                      <StatusBadge status="absent"/>
                    ) : isEnrolled ? (
                      <span className="status-badge" style={{background:'#eef4f8',color:'#3a5570'}}>Eligible</span>
                    ) : (
                      <span className="status-badge" style={{background:'#f8f9fa',color:'#8c9ba8'}}>Unenrolled</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  </>;
}


/* ── Schedule ────────────────────────────────────────────────── */

function Schedule({state, refresh, action, setToast, setError}) {
  const [activeTab, setActiveTab] = useState('weekly');
  const [editRule, setEditRule] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [editBusy, setEditBusy] = useState(false);
  const [cancelModal, setCancelModal] = useState(null);
  const [cancelDate, setCancelDate] = useState(state.today || '');
  const [cancelReason, setCancelReason] = useState('');
  const timetable = state.timetable || [];
  const exceptions = state.exceptions || [];

  const grouped = {};
  for (const rule of timetable) {
    const day = rule.weekday;
    if (!grouped[day]) grouped[day] = [];
    grouped[day].push(rule);
  }
  for (const day in grouped) {
    grouped[day].sort((a,b) => a.start_time.localeCompare(b.start_time));
  }

  // Collect all unique time slots across all days for the grid rows
  const allSlots = [];
  const slotSet = new Set();
  for (const rule of timetable) {
    const key = `${rule.start_time}-${rule.end_time}`;
    if (!slotSet.has(key)) {
      slotSet.add(key);
      allSlots.push({start: rule.start_time, end: rule.end_time});
    }
  }
  allSlots.sort((a,b) => a.start.localeCompare(b.start));

  function openEdit(rule) {
    setEditRule(rule);
    setEditForm({
      course_name: rule.course_name,
      course_code: rule.course_code || '',
      teacher: rule.teacher || '',
      room: rule.room || '',
      start_time: rule.start_time,
      end_time: rule.end_time,
      batch: rule.batch || '',
      is_lab: !!rule.is_lab,
    });
  }

  async function saveEdit(e) {
    e.preventDefault();
    setEditBusy(true);
    try {
      await api(`/timetable/${editRule.id}`, {method:'PUT', body: editForm});
      await refresh();
      setEditRule(null);
      setToast('Timetable updated.');
    } catch(err) { setError(err.message); }
    finally { setEditBusy(false); }
  }

  async function cancelClass(e) {
    e.preventDefault();
    try {
      await api('/timetable/exceptions', {method:'POST', body:{
        rule_id: cancelModal.id,
        date: cancelDate,
        action: 'cancel',
        reason: cancelReason || null
      }});
      await refresh();
      setCancelModal(null);
      setCancelReason('');
      setToast('Class cancelled for that date.');
    } catch(err) { setError(err.message); }
  }

  function getClassesForSlot(day, slot) {
    return (grouped[day] || []).filter(r => r.start_time === slot.start && r.end_time === slot.end);
  }

  return <>
    <div className="tab-bar">
      <button className={activeTab === 'weekly' ? 'tab active' : 'tab'} onClick={() => setActiveTab('weekly')}>
        <BookOpen size={15}/>Weekly timetable
      </button>
      <button className={activeTab === 'exceptions' ? 'tab active' : 'tab'} onClick={() => setActiveTab('exceptions')}>
        <AlertTriangle size={15}/>Exceptions ({exceptions.length})
      </button>
    </div>

    {activeTab === 'weekly' && <>
      <div className="tt-grid-wrap">
        <table className="tt-grid">
          <thead>
            <tr>
              <th className="tt-time-col">Time</th>
              {[0,1,2,3,4,5].map(d =>
                <th key={d} className={state.weekday === d ? 'tt-day-head tt-today' : 'tt-day-head'}>
                  {DAY_NAMES[d]}
                  {state.weekday === d && <span className="today-badge">Today</span>}
                </th>
              )}
            </tr>
          </thead>
          <tbody>
            {allSlots.map(slot => {
              const slotKey = `${slot.start}-${slot.end}`;
              return <tr key={slotKey}>
                <td className="tt-time-cell">
                  <span className="tt-time-start">{slot.start}</span>
                  <span className="tt-time-sep">–</span>
                  <span className="tt-time-end">{slot.end}</span>
                </td>
                {[0,1,2,3,4,5].map(day => {
                  const classes = getClassesForSlot(day, slot);
                  return <td key={day} className={`tt-cell ${state.weekday === day ? 'tt-today-col' : ''}`}>
                    {classes.length ? classes.map(rule =>
                      <div key={rule.id} className={`tt-card ${rule.is_lab ? 'tt-lab' : 'tt-lecture'}`}>
                        <div className="tt-card-name">{rule.course_name}</div>
                        <div className="tt-card-info">
                          {rule.teacher && <span>{rule.teacher}</span>}
                          {rule.room && <span>📍 {rule.room}</span>}
                        </div>
                        <div className="tt-card-footer">
                          <span className="batch-tag">{rule.batch || 'All D'}</span>
                          <div className="tt-card-actions">
                            <button className="tt-action-btn" title="Edit class" onClick={() => openEdit(rule)}><Pencil size={12}/></button>
                            <button className="tt-action-btn tt-cancel-btn" title="Cancel on a date" onClick={() => { setCancelModal(rule); setCancelDate(state.today); }}><X size={12}/></button>
                          </div>
                        </div>
                      </div>
                    ) : <div className="tt-empty">—</div>}
                  </td>;
                })}
              </tr>;
            })}
          </tbody>
        </table>
      </div>
      <div className="tt-legend">
        <span><i className="tt-dot tt-lecture-dot"/>Lecture</span>
        <span><i className="tt-dot tt-lab-dot"/>Lab</span>
      </div>
    </>}

    {activeTab === 'exceptions' && <section className="panel">
      <div className="panel-heading"><h2>Schedule exceptions</h2></div>
      {exceptions.length ? <div className="table-scroll"><table><thead><tr><th>Date</th><th>Action</th><th>Reason</th><th>Actions</th></tr></thead>
        <tbody>{exceptions.map(e =>
          <tr key={e.id}>
            <td><b>{e.date}</b></td>
            <td><StatusBadge status={e.action === 'cancel' ? 'absent' : 'present'}/></td>
            <td>{e.reason || '—'}</td>
            <td><button className="icon-button delete" aria-label="Remove exception" onClick={() => action(() => api(`/timetable/exceptions/${e.id}`, {method:'DELETE'}), 'Exception removed.')}><Trash2 size={17}/></button></td>
          </tr>
        )}</tbody>
      </table></div> : <Empty icon={Calendar}>No schedule exceptions yet. Cancel or swap classes from the weekly view.</Empty>}
    </section>}

    {/* Edit modal */}
    {editRule && <div className="modal-backdrop" onClick={() => setEditRule(null)}>
      <section className="modal edit-modal" onClick={e => e.stopPropagation()}>
        <h2><Pencil size={18}/> Edit class</h2>
        <form onSubmit={saveEdit}>
          <label>Course name<input value={editForm.course_name} onChange={e => setEditForm({...editForm, course_name: e.target.value})} required/></label>
          <label>Course code<input value={editForm.course_code} onChange={e => setEditForm({...editForm, course_code: e.target.value})}/></label>
          <div className="form-row">
            <label>Start time<input type="time" value={editForm.start_time} onChange={e => setEditForm({...editForm, start_time: e.target.value})}/></label>
            <label>End time<input type="time" value={editForm.end_time} onChange={e => setEditForm({...editForm, end_time: e.target.value})}/></label>
          </div>
          <div className="form-row">
            <label>Teacher<input value={editForm.teacher} onChange={e => setEditForm({...editForm, teacher: e.target.value})}/></label>
            <label>Room<input value={editForm.room} onChange={e => setEditForm({...editForm, room: e.target.value})}/></label>
          </div>
          <div className="form-row">
            <label>Batch<input value={editForm.batch} placeholder="Leave empty for all" onChange={e => setEditForm({...editForm, batch: e.target.value})}/></label>
            <label className="checkbox-label"><input type="checkbox" checked={editForm.is_lab} onChange={e => setEditForm({...editForm, is_lab: e.target.checked})}/> Lab session</label>
          </div>
          <div className="button-row">
            <button type="button" className="outline" onClick={() => setEditRule(null)}>Cancel</button>
            <button disabled={editBusy}>{editBusy ? 'Saving…' : 'Save changes'}</button>
          </div>
        </form>
      </section>
    </div>}

    {/* Cancel modal */}
    {cancelModal && <div className="modal-backdrop" onClick={() => setCancelModal(null)}>
      <section className="modal" onClick={e => e.stopPropagation()}>
        <h2>Cancel class</h2>
        <p>Cancel <b>{cancelModal.course_name}</b> ({DAY_NAMES[cancelModal.weekday]} {cancelModal.start_time}–{cancelModal.end_time}) on a specific date.</p>
        <form onSubmit={cancelClass}>
          <label>Date<input type="date" value={cancelDate} onChange={e => setCancelDate(e.target.value)} required/></label>
          <label>Reason (optional)<input value={cancelReason} onChange={e => setCancelReason(e.target.value)} placeholder="e.g. Holiday, faculty leave"/></label>
          <div className="button-row">
            <button type="button" className="outline" onClick={() => setCancelModal(null)}>Back</button>
            <button className="danger">Cancel this class</button>
          </div>
        </form>
      </section>
    </div>}
  </>;
}


/* ── Students ────────────────────────────────────────────────── */

function Students({state, enroll, confirm, refresh, setToast, setError}) {
  const [search,setSearch] = useState('');
  const [batchFilter,setBatchFilter] = useState('all');

  // Extract numeric part from roll_no for sorting (D-1 → 1, D-12 → 12)
  function rollNum(rollNo) {
    const m = rollNo?.match(/(\d+)/);
    return m ? parseInt(m[1], 10) : 9999;
  }

  const students = state.students
    .filter(s => {
      const matchSearch = (s.name + ' ' + s.roll_no).toLowerCase().includes(search.toLowerCase());
      const matchBatch = batchFilter === 'all' || s.batch === batchFilter;
      return matchSearch && matchBatch;
    })
    .sort((a, b) => rollNum(a.roll_no) - rollNum(b.roll_no));

  return <>
    <div className="section-toolbar">
      <div className="filter-group">
        <div className="search"><Search size={18}/><input aria-label="Search students" placeholder="Search name or roll number" value={search} onChange={e => setSearch(e.target.value)}/></div>
        <select aria-label="Filter by batch" value={batchFilter} onChange={e => setBatchFilter(e.target.value)}>
          <option value="all">All batches</option>
          <option value="D1">Batch D1</option>
          <option value="D2">Batch D2</option>
          <option value="D3">Batch D3</option>
        </select>
      </div>
      <span className="muted">{state.students.length} students · {state.students.filter(s => s.sample_count > 0).length} enrolled</span>
    </div>

    <section className="panel">
      <div className="table-scroll"><table><thead><tr>
        <th>Photo</th><th>Student Name</th><th>Roll No</th><th>Email</th><th>Section</th><th>Samples</th><th>Batch</th><th>Actions</th>
      </tr></thead>
        <tbody>{students.map(s =>
          <tr key={s.id}>
            <td><span className="avatar">{s.photo_path ? <img src={s.photo_path} alt="" className="avatar-img"/> : s.name?.[0]?.toUpperCase()}</span></td>
            <td><b>{s.name}</b>{s.consent_at && <small className="enrolled-badge">Enrolled</small>}</td>
            <td>{s.roll_no}</td>
            <td><span className="email-cell">{s.email || '—'}</span></td>
            <td>{s.section}</td>
            <td>{s.sample_count > 0 ? <span className="score">{s.sample_count} captures</span> : <span className="muted">Not enrolled</span>}</td>
            <td><span className="batch-tag">{s.batch || '—'}</span></td>
            <td>
              <button className="icon-button delete" aria-label={`Delete ${s.name}`}
                onClick={() => confirm({
                  title: `Delete ${s.name}?`,
                  description: 'This removes their embeddings and attendance records. It also clears the current evaluation and calibration because the enrolled gallery changes.',
                  run: () => api(`/students/${s.id}`, {method:'DELETE'})
                })}><Trash2 size={17}/></button>
            </td>
          </tr>
        )}</tbody>
      </table></div>
      {!students.length && <>
        <Empty icon={Users}>{search || batchFilter !== 'all' ? 'No students match your filters.' : 'No students in the database yet.'}</Empty>
        {!search && batchFilter === 'all' && <div className="center-action"><button onClick={enroll}><UserPlus size={17}/>Enroll first student</button></div>}
      </>}
    </section>

    <div className="info-strip"><ShieldCheck size={20}/><div><b>Consent comes first</b><p>Face embeddings stay on this computer. They are sensitive biometric data. Students can request deletion at any time.</p></div></div>
  </>;
}


/* ── Enrollment ──────────────────────────────────────────────── */

function Enrollment({state, onDone, back, setError}) {
  const [studentId, setStudentId] = useState('');
  const [consent, setConsent] = useState(false);
  const [tokens, setTokens] = useState([]);
  const [result, setResult] = useState(null);
  const [saving, setSaving] = useState(false);
  const [localError, setLocalError] = useState('');
  const [uploadMode, setUploadMode] = useState('camera');
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef(null);

  const unenrolledStudents = (state?.students || []).filter(s => s.sample_count === 0);
  const selectedStudent = (state?.students || []).find(s => s.id === studentId);

  const prompts = [
    'Look straight ahead in even lighting',
    'Turn slightly to your left',
    'Turn slightly to your right',
    'Raise your chin slightly',
    'Lower your chin slightly',
    'Try a modest change in lighting',
  ];

  async function capture(image) {
    if (!studentId) throw new Error('Select a student first');
    const r = await api(`/students/${studentId}/enrollment/sample`, {method:'POST', body:{image, consent}});
    setResult(r);
    if (!r.token) throw new Error(r.reason);
    setTokens(v => [...v, r.token]);
  }

  async function handleFileUpload(e) {
    const files = e.target.files;
    if (!files?.length || !studentId) return;
    setUploading(true);
    setLocalError('');
    try {
      for (const file of files) {
        const fd = new FormData();
        fd.append('file', file);
        fd.append('consent', 'true');
        const r = await uploadFile(`/students/${studentId}/upload`, fd);
        if (r.ok) {
          setTokens(prev => [...prev, ...(new Array(r.samples || 1).fill('uploaded'))]);
        }
      }
      await onDone();
    } catch (e) {
      setLocalError(e.message);
    } finally {
      setUploading(false);
    }
  }

  async function save(e) {
    e.preventDefault();
    setSaving(true);
    setLocalError('');
    try {
      await api(`/students/${studentId}/enrollment/save`, {method:'POST', body:{consent, tokens: tokens.filter(t => t !== 'uploaded')}});
      await onDone();
    } catch (e) {
      setLocalError(e.message);
    } finally {
      setSaving(false);
    }
  }

  const realTokens = tokens.filter(t => t !== 'uploaded');
  const hasUploaded = tokens.some(t => t === 'uploaded');

  return <>
    <button className="back-link" onClick={back}><ArrowLeft size={16}/>Back to students</button>
    <div className="workspace enrollment">
      <div className="enroll-left">
        {/* Mode toggle */}
        <div className="upload-toggle">
          <button className={uploadMode === 'camera' ? 'active' : ''} onClick={() => setUploadMode('camera')}><CameraIcon size={16}/>Live camera</button>
          <button className={uploadMode === 'upload' ? 'active' : ''} onClick={() => setUploadMode('upload')}><Upload size={16}/>Upload from device</button>
        </div>

        {uploadMode === 'camera' ?
          <Camera onFrame={capture} enabled={consent && !!studentId && tokens.length < 15} result={result} actionLabel={`Capture sample ${tokens.length + 1}`}/>
        :
          <section className="panel upload-panel">
            <div className="upload-zone" onClick={() => consent && studentId && fileRef.current?.click()}>
              <input ref={fileRef} type="file" accept="image/*,video/*" multiple onChange={handleFileUpload} className="hidden"/>
              {uploading ? <>
                <div className="upload-spinner"/>
                <h3>Processing…</h3>
                <p>Extracting face embeddings from your files.</p>
              </> : <>
                <Upload size={48} strokeWidth={1.3}/>
                <h3>Upload photos or video</h3>
                <p>Drop image or video files here, or click to browse. Each file should contain one clearly visible face.</p>
                <button disabled={!consent || !studentId} onClick={e => { e.stopPropagation(); fileRef.current?.click(); }}>
                  <FileVideo size={16}/>Choose files
                </button>
              </>}
            </div>
            <p className="caption"><Info size={15}/> Accepted: JPEG, PNG images and MP4 video (max 10 MB each). Video is sampled at 1 frame/second.</p>
          </section>
        }
      </div>

      <form className="panel controls" onSubmit={save}>
        <h2>Student enrollment</h2>

        <label>Select student
          <select value={studentId} onChange={e => { setStudentId(e.target.value); setTokens([]); setResult(null); }}>
            <option value="">Choose a student…</option>
            {(state?.students || []).map(s =>
              <option key={s.id} value={s.id}>{s.name} · {s.roll_no}{s.sample_count > 0 ? ' (already enrolled)' : ''}</option>
            )}
          </select>
        </label>

        {selectedStudent && <div className="selected-student-info">
          <span className="avatar">{selectedStudent.name?.[0]?.toUpperCase()}</span>
          <div>
            <b>{selectedStudent.name}</b>
            <small>{selectedStudent.roll_no} · {selectedStudent.section} · {selectedStudent.batch || '—'}</small>
          </div>
        </div>}

        <label className="consent">
          <input type="checkbox" checked={consent} onChange={e => setConsent(e.target.checked)}/>
          <span>I have explained the local attendance demonstration and data deletion process. This student explicitly consents to face capture and embedding storage.</span>
        </label>

        <div className="divider"/>
        <div className="panel-heading"><h3>Guided capture</h3><span className="score">{tokens.length} / 5 minimum</span></div>
        <div className="progress-track"><div style={{width:`${Math.min(tokens.length / 5 * 100, 100)}%`}}/></div>
        <p className="capture-prompt">{tokens.length < 15 ? prompts[Math.min(tokens.length, 5)] : 'Capture complete. Save the enrollment.'}</p>
        <p className="muted small">Capture 5–15 distinct views via camera or upload. Keep the same person in frame. Camera samples expire after 10 minutes.</p>

        {localError && <div className="inline-error" role="alert">{localError}</div>}

        {!hasUploaded && <button className="full" disabled={saving || !consent || realTokens.length < 5 || !studentId}>
          <UserPlus size={17}/>{saving ? 'Saving…' : 'Save enrollment'}
        </button>}

        <button type="button" className="text-button" disabled={!tokens.length}
          onClick={() => { setTokens([]); setResult(null); }}>Reset captures</button>

        <p className="caption"><Info size={15}/> Only embeddings are saved. Enrollment changes reset evaluation and calibration.</p>
      </form>
    </div>
  </>;
}


/* ── Attendance Records ──────────────────────────────────────── */

function Records({state}) {
  const [selectedDate, setSelectedDate] = useState(state.today || new Date().toISOString().slice(0,10));
  const [selectedSession, setSelectedSession] = useState('');
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(false);

  // Filter sessions by selected date
  const dateSessions = (state.sessions || []).filter(s => s.date === selectedDate);

  useEffect(() => {
    if (dateSessions.length && !selectedSession) {
      setSelectedSession(dateSessions[0].id);
    }
  }, [selectedDate]);

  useEffect(() => {
    if (!selectedSession) { setRecords([]); return; }
    setLoading(true);
    api(`/attendance?session_id=${selectedSession}&date=${selectedDate}`)
      .then(r => { setRecords(r); setLoading(false); })
      .catch(() => setLoading(false));
  }, [selectedSession, selectedDate]);

  return <>
    <div className="section-toolbar">
      <div className="filter-group">
        <label className="inline-label">Date
          <input type="date" value={selectedDate} onChange={e => { setSelectedDate(e.target.value); setSelectedSession(''); }}/>
        </label>
        <label className="inline-label">Class / Session
          <select value={selectedSession} onChange={e => setSelectedSession(e.target.value)}>
            <option value="">Select a session…</option>
            {dateSessions.map(s => <option key={s.id} value={s.id}>{s.name}{s.ended_at ? '' : ' (active)'}</option>)}
          </select>
        </label>
      </div>
      {selectedSession && <a className="button outline" href={`/api/attendance.csv?session_id=${selectedSession}&date=${selectedDate}`}>
        <Download size={17}/>Export CSV
      </a>}
    </div>

    <section className="panel">
      <div className="panel-heading">
        <h2>Attendance log</h2>
        <span className="muted">{records.length} entries{records.length > 0 && ` · ${records.filter(r => r.status === 'present').length} present · ${records.filter(r => r.status === 'absent').length} absent`}</span>
      </div>

      {loading ? <Empty>Loading attendance data…</Empty> :
        records.length ? <div className="table-scroll"><table><thead><tr>
          <th>Student Name</th><th>ID / Roll No</th><th>Section</th><th>Session</th><th>Time</th><th>Status</th>
        </tr></thead>
          <tbody>{records.map(r =>
            <tr key={r.student_id + r.session_id}>
              <td><span className="avatar">{r.student_name?.[0]?.toUpperCase()}</span><b>{r.student_name}</b></td>
              <td>{r.roll_no}</td>
              <td>{r.section}</td>
              <td>{r.session_name}</td>
              <td>{r.status === 'present' ? timeLabel(r.marked_at) : '—'}</td>
              <td><StatusBadge status={r.status}/></td>
            </tr>
          )}</tbody>
        </table></div>
      : <Empty icon={ClipboardList}>{selectedSession ? 'No attendance records for this session.' : 'Select a date and session to view attendance.'}</Empty>}
    </section>
    <p className="caption">One entry per student per session. Times are in your browser's local timezone; exports use UTC.</p>
  </>;
}


/* ── Accuracy Lab (Deep Learning Metrics Dashboard) ──────────── */

/* ── Mount ───────────────────────────────────────────────────── */

createRoot(document.getElementById('root')).render(<App/>);
