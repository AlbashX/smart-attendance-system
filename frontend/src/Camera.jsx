import { useEffect, useRef, useState } from 'react';
import { Camera as CameraIcon, Video, Square, Info, SwitchCamera } from 'lucide-react';

export default function Camera({ onFrame, automatic = false, enabled = true, result, actionLabel = 'Capture sample' }) {
  const video = useRef(null), stream = useRef(null), canvas = useRef(null), handler = useRef(onFrame);
  const alive = useRef(true), running = useRef(false), busy = useRef(false);
  const [active, setActive] = useState(false), [working, setWorking] = useState(false), [error, setError] = useState('');

  // Default to back camera ('environment') on mobile devices for scanning, and 'user' on desktop
  const isMobile = typeof navigator !== 'undefined' && /Android|iPhone|iPad|iPod/i.test(navigator.userAgent || '');
  const [facingMode, setFacingMode] = useState(isMobile ? 'environment' : 'user');
  const [aspectRatio, setAspectRatio] = useState(isMobile ? '3 / 4' : '4 / 3');

  handler.current = onFrame;

  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
      running.current = false;
      stream.current?.getTracks().forEach(t => t.stop());
    };
  }, []);

  const stop = () => {
    running.current = false;
    stream.current?.getTracks().forEach(t => t.stop());
    stream.current = null;
    setActive(false);
  };

  useEffect(() => {
    if (!enabled && active) stop();
  }, [enabled, active]);

  async function start(mode = facingMode) {
    setError('');
    setWorking(true);
    if (stream.current) {
      stream.current.getTracks().forEach(t => t.stop());
      stream.current = null;
    }
    try {
      const constraints = {
        video: {
          facingMode: { ideal: mode },
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false,
      };
      let media;
      try {
        media = await navigator.mediaDevices.getUserMedia(constraints);
      } catch (err) {
        media = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      }

      if (!alive.current) {
        media.getTracks().forEach(t => t.stop());
        return;
      }
      stream.current = media;
      if (video.current) {
        video.current.srcObject = media;
        await video.current.play();
      }
      running.current = true;
      setActive(true);
    } catch (e) {
      stream.current?.getTracks().forEach(t => t.stop());
      setError('Camera unavailable. Allow camera access and close other apps using it.');
    } finally {
      if (alive.current) setWorking(false);
    }
  }

  async function flipCamera() {
    const nextMode = facingMode === 'user' ? 'environment' : 'user';
    setFacingMode(nextMode);
    if (active) {
      await start(nextMode);
    }
  }

  const handleLoadedMetadata = () => {
    const v = video.current;
    if (v && v.videoWidth && v.videoHeight) {
      setAspectRatio(`${v.videoWidth} / ${v.videoHeight}`);
    }
  };

  async function capture() {
    if (busy.current || !running.current || !video.current?.videoWidth) return;
    busy.current = true;
    if (alive.current) setWorking(true);
    try {
      const v = video.current, c = canvas.current;
      const maxDim = Math.max(v.videoWidth, v.videoHeight);
      const scale = Math.min(1, 640 / maxDim);
      c.width = Math.round(v.videoWidth * scale);
      c.height = Math.round(v.videoHeight * scale);
      c.getContext('2d').drawImage(v, 0, 0, c.width, c.height);
      await handler.current(c.toDataURL('image/jpeg', 0.85));
      if (alive.current) setError('');
    } catch (e) {
      if (alive.current) setError(e.message);
    } finally {
      busy.current = false;
      if (alive.current) setWorking(false);
    }
  }

  useEffect(() => {
    if (!automatic || !active || !enabled) return;
    const timer = setInterval(capture, 450);
    return () => clearInterval(timer);
  }, [automatic, active, enabled]);

  return (
    <section className="panel camera-panel">
      <div className="panel-heading">
        <h2>Camera preview</h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className={`status ${active ? 'online' : ''}`}>
            <i />
            {active ? `Live (${facingMode === 'environment' ? 'Rear' : 'Front'})` : 'Offline'}
          </span>
          <button
            type="button"
            className="icon-button"
            title="Switch front/rear camera"
            onClick={flipCamera}
            style={{ padding: '5px', cursor: 'pointer', borderRadius: '4px' }}
          >
            <SwitchCamera size={17} />
          </button>
        </div>
      </div>
      <div className="camera-stage" style={{ aspectRatio, maxHeight: '600px' }}>
        <video
          ref={video}
          muted
          playsInline
          onLoadedMetadata={handleLoadedMetadata}
          className={active ? '' : 'hidden'}
          style={{ width: '100%', height: '100%', objectFit: 'contain' }}
        />
        {!active && (
          <div className="camera-empty">
            <CameraIcon size={54} strokeWidth={1.3} />
            <h3>Your camera is off</h3>
            <p>{enabled ? 'Start the camera to begin scanning.' : 'Complete consent before starting the camera.'}</p>
            <button onClick={() => start(facingMode)} disabled={!enabled || working}>
              <Video size={17} />
              {working ? 'Opening camera…' : 'Start camera'}
            </button>
          </div>
        )}
        <div className="frame-corners" aria-hidden="true"><i /><i /><i /><i /></div>
        {active && result?.box && (
          <div
            className={`face-box ${result.identity ? 'matched' : ''}`}
            style={{
              left: `${(result.box[0] / result.width) * 100}%`,
              top: `${(result.box[1] / result.height) * 100}%`,
              width: `${(result.box[2] / result.width) * 100}%`,
              height: `${(result.box[3] / result.height) * 100}%`,
            }}
          >
            <span>{result.name || (result.quality ? 'Face detected' : 'Adjust position')}</span>
          </div>
        )}
        {active && (
          <div className="camera-toolbar">
            <span>{working ? 'Scanning…' : result?.reason || 'Position face inside the frame'}</span>
            <div className="camera-toolbar-actions">
              <button type="button" className="camera-flip" onClick={flipCamera} title="Switch camera">
                <SwitchCamera size={13} /> Flip
              </button>
              <button type="button" className="camera-stop" onClick={stop}>
                <Square size={13} /> Stop
              </button>
            </div>
          </div>
        )}
      </div>
      <canvas ref={canvas} className="hidden" />
      {error && <div className="inline-error" role="alert">{error}</div>}
      {active && !automatic && (
        <button className="capture-button" disabled={!enabled || working} onClick={capture}>
          <CameraIcon size={17} />
          {working ? 'Checking quality…' : actionLabel}
        </button>
      )}
      <p className="caption">
        <Info size={15} /> Frames are processed locally in real time.
      </p>
    </section>
  );
}
