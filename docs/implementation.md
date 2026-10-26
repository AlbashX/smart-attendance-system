# Local attendance prototype

User authorized implementation on 2026-10-26. Local browser UI, Python FastAPI, React/Vite, SQLite, YuNet 2023 + SFace 2021 ONNX. One supervised person at a time. Frozen pretrained inference, no claim of local training or measured accuracy before evaluation.

## Milestones and acceptance checks
1. Matching and persistence: normalized centroid matching, unknown threshold, ambiguity margin, three consecutive observations, unique student/session attendance across restarts. Unit tests use synthetic vectors, not accuracy claims.
2. Real inference: load downloaded OpenCV models, reject missing/multiple/small/blurry/poorly lit faces, align using YuNet landmarks. Images only in memory. Serialize inference to protect OpenCV shared state.
3. Enrollment: explicit consent, five or more captures, consistency checks, store numeric embeddings and centroid; deletion cascades attendance and invalidates evaluation.
4. Local UI: live camera, volunteer enrollment, sessions, records/export, accuracy lab. Browser camera starts only on user action. No cloud services or external fonts at runtime.
5. Evaluation: labeled independent validation/test attempts; calibrate threshold on validation only; report test known recognition, unknown rejection, FAR/FRR for verification separately, count wrong identities, latency and sample counts. Gallery changes invalidate previous calibration/probes. LFW CLI uses supplied data, no automatic biometric dataset download.
6. Verify Python tests, frontend build, model smoke test, API integration and browser UX. Volunteer recognition accuracy and actual webcam end-to-end validation require consenting users.

## UI design
White canvas, slate sidebar, navy camera surface, teal actions. Four areas: Live attendance, Volunteers, Attendance records, Accuracy lab. Honest empty states. No seeded people or invented metrics. Responsive navigation and accessible labeled controls.

## Boundaries
Loopback-only supervised single-operator prototype, no production authentication or anti-spoofing. Not suitable for actual access control or unsupervised attendance. Embeddings are sensitive, unencrypted local data; filesystem access must be restricted. No image persistence. No remote deployment until authentication, transport encryption and privacy review are added.
