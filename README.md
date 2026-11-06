# Attend — local face recognition attendance prototype

Current deployment: source code is backed up in a private GitHub repository; the Python backend and database stay on your laptop. For password-protected HTTPS access from a phone on the same Wi-Fi, follow [Mobile access](docs/mobile-access.md) and run `start-mobile.ps1` alongside `start.ps1`. GitHub Pages cannot run this Python backend. The new live/spoof training work is a proposal: see [Training and evaluation plan](docs/dl-training-and-evaluation-plan.md). Older descriptions below predate the student/timetable update.

A Deep Learning capstone application built with React, FastAPI, YuNet and SFace. Real pretrained ONNX inference, landmark alignment, cosine matching, consent-based enrollment, persistent attendance and a validation/test accuracy lab. No fabricated students or accuracy numbers.

## Start on Windows

Prerequisites: Python 3.11+ and Node.js 20.19+ (only needed to build the UI).

```powershell
cd D:\capstone
.\setup.ps1
.\start.ps1
```

Open http://127.0.0.1:8000 in Chrome or Edge. If PowerShell execution policy prevents scripts, run `powershell -ExecutionPolicy Bypass -File .\start.ps1` for that invocation. Stop with Ctrl+C. After initial setup, `start.ps1` is enough. Models and frontend run locally without an internet connection. Bind to loopback only; do not expose this prototype to a network.

## First demonstration

1. Open **Volunteers → Enroll volunteer**. Explain the purpose, storage and deletion procedure; obtain explicit consent.
2. Enter the participant name and student ID, record consent, then start the camera. Capture at least five distinct views, preferably 10–15 across modest pose and lighting variation. Save the participant. Raw images are not persisted. Unsaved embedding captures expire after ten minutes.
3. Enroll at least two volunteers. Only one person should appear in the camera at a time.
4. Open **Live attendance**, name and start a session, then start the camera. Three consecutive accepted observations trigger one record per volunteer/session. Returning or restarting does not create duplicates.
5. Test an additional consenting, unenrolled volunteer. The system should show Unknown rather than mark attendance. Incorrect acceptance is a failure to record and investigate, not a result to hide.
6. End the session. View **Attendance records** and export CSV. Timestamps are stored in UTC and displayed in browser local time.

## Accuracy comes from experiments

The default similarity threshold **0.45** and ambiguity margin **0.08** are provisional engineering choices, not measured guarantees. Enrollment creates normalized centroids from multiple normalized SFace embeddings. Matching takes the highest cosine similarity, rejects scores below threshold and rejects insufficient separation from the second-best identity. Three-frame consistency is not liveness detection.

**Accuracy lab** implements a local experiment:

- Collect labeled validation attempts from known and consenting unknown volunteers. Use a new capture session from enrollment. Choose ground truth before capture; incorrect labels invalidate results.
- Minimum five known and five unknown attempts permits calibration, but this is only a software minimum. Aim for substantially more attempts per condition and volunteer; report subject counts, lighting, pose and capture days.
- Calibrate once: select a threshold using maximum impostor scores per attempt, targeting observed validation false-match rate <=1%. A small dataset cannot substantiate a population-wide 1% rate. The ambiguity margin is fixed and may further reject attempts.
- Calibration freezes validation. Collect held-out test attempts in a different batch, using different unknown volunteers. Never adjust parameters after inspecting test outcomes without defining a new held-out test set.
- Reports include known identification accuracy (rejections count as failures), unknown rejection accuracy, wrong-identity count, pairwise verification accuracy/FAR/FRR with comparison counts, and median/p95 extraction latency. Pairwise comparisons are correlated; do not treat them as independent trials.
- Quality-failed captures are not saved as scored attempts. Log capture failures separately in your project report. Latency covers decode, detection and feature extraction; it excludes network round trip, gallery matching and multi-frame confirmation time.
- Adding/deleting volunteers resets calibration and probes because the gallery changed. Reset experiment deletes only probes/calibration, not volunteers or attendance.

Suggested comparisons: one versus several enrollment samples; frontal/even lighting versus pose/lighting variation; different thresholds; single-frame versus three-frame decisions. Keep separate held-out sets for final claims. The UI currently uses centroid matching and three-frame confirmation; alternative strategies should be added as explicit experiment configurations, not silently changed.

### LFW verification

LFW is not included or automatically downloaded. Obtain the original dataset and official `pairs.txt` from its source under applicable terms. Run:

```powershell
.\.venv\Scripts\python.exe scripts\evaluate_lfw.py --images D:\datasets\lfw --pairs D:\datasets\pairs.txt --output data\lfw_report.json
```

The script requires the official 6000-pair, ten-fold file. Each fold uses a threshold selected on the other nine folds. It reports quality/detection failures, end-to-end accuracy counting failed pairs as incorrect, and conditional verification metrics for valid pairs. It uses the local quality gate, so it is not an exact reproduction of published SFace scores. Pretraining overlap is not audited. An LFW result is not a substitute for local open-set testing.

## Architecture and files

```text
Browser camera (explicit start)
  → JPEG over loopback → image validation → YuNet + facial landmarks
  → face-size / blur / lighting checks → aligned SFace embedding
  → L2 normalization → cosine centroid matching + ambiguity check
  → consecutive-frame confirmation → unique SQLite attendance entry
```

- `backend/vision.py`: actual models, image decoding, quality gates and alignment.
- `backend/core.py`: matching, temporal confirmation, threshold calibration and metrics.
- `backend/store.py`: SQLite persistence and atomic uniqueness constraints.
- `backend/main.py`: validated HTTP API, consent workflow, calibration, exports and static UI.
- `frontend/src/`: React interface and camera lifecycle.
- `scripts/download_models.py`: official OpenCV Zoo downloads with recorded SHA-256 provenance.
- `scripts/evaluate_lfw.py`: fold-separated benchmark runner.
- `tests/`: synthetic-vector logic tests, isolated API tests and real-model blank-frame smoke test.
- `data/`: local SQLite database; excluded from Git.

The backend is deliberately one process/worker because ephemeral capture tokens and observation history are in memory. SQLite has foreign keys, WAL, and a session/student unique key. Modules provide extension points for other models, matching strategies and a future database service. Scaling to multiple workers requires shared observation/token state and a security design; do not add `--workers` to this prototype.

## Tests and development

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
cd frontend
npm.cmd run build
```

For development run the Python API on port 8000 and Vite on port 5173. Use the production build for the normal demonstration. The same-origin guard intentionally rejects mismatched Origin headers; use `VITE` proxy with changeOrigin as configured, or build before testing.

## Privacy and limitations

- Embeddings are sensitive biometric data, not anonymous or guaranteed irreversible. Local SQLite is **not encrypted**; restrict OS access, avoid syncing/backing up biometric data without consent, and delete it at the agreed retention date.
- UI consent records an operator attestation with timestamp, not a legal consent document. Maintain an appropriate participant information/consent process separately.
- Deleting a participant deletes their embeddings and attendance rows. This is logical deletion, not a guarantee of forensic erasure from storage/backups.
- No raw frames are saved by the application. In-memory data is not claimed to be securely wiped.
- No liveness or presentation-attack protection. A photo or screen replay may be accepted. Use only consenting adults in supervised demonstrations; do not make real attendance or access-control decisions from this prototype.
- No login or multi-user administration. Same-origin and host restrictions reduce accidental exposure but are not authentication. Use only on a trusted local computer.
- Camera permissions and real volunteer end-to-end accuracy need to be verified on the target laptop. Automated synthetic tests do not establish biometric accuracy.

- Live Demo- https://smart-attendance-system-kk8h.onrender.com/

## Sources

- [OpenCV YuNet/SFace tutorial](https://docs.opencv.org/4.x/d0/dd4/tutorial_dnn_face.html)
- [OpenCV Zoo YuNet model and licensing](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet)
- [OpenCV Zoo SFace model and licensing](https://github.com/opencv/opencv_zoo/tree/main/models/face_recognition_sface)
- [SFace paper](https://arxiv.org/abs/2205.12010)
- [LFW protocols](https://people.cs.umass.edu/~elm/papers/lfw_update.pdf)

Review each model's license before redistribution. Model files are excluded from Git; `models/manifest.json` records their download source and checksum.
