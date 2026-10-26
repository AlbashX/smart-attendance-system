# Verification record

## Automated checks
- 14 Python tests pass: normalization, unknown/ambiguous rejection, stability reset, metric denominators, attendance uniqueness after database reopen, one active session, explicit consent, unique enrollment tokens, API recognition confirmation, calibration/test separation, gallery invalidation, invalid images, cross-origin/host rejection, actual YuNet blank-frame inference, actual SFace forward pass on a synthetic crop, closed-session protection and CSV formula escaping.
- Actual YuNet and SFace ONNX models load in OpenCV. Blank-frame inference returns no face, no attendance. A synthetic crop produces a finite normalized 128-dimensional SFace vector; this checks runtime compatibility only.
- React/Vite production build passes. Dependencies captured in frontend/package-lock.json and requirements-lock.txt.
- LFW CLI help runs. Full LFW evaluation was not run because no LFW dataset was supplied.
- API tests use isolated temporary databases and synthetic vectors for recognition logic. They do not measure human face recognition accuracy.

## Browser checks
In-app browser: live screen renders; enrollment camera and save disabled without consent/samples; accuracy lab has honest empty metrics and rejects calibration without enough attempts. Navigation reviewed. Compact-navigation accessible names fixed.

Chrome DevTools MCP: 1440 x 1000 desktop and 390 x 844 mobile viewport checked; neither has horizontal document overflow. Desktop screenshot saved in docs/ui-desktop.png. Camera hardware permissions were not granted or exercised automatically.

## Design comparison
Compared generated docs/ui-concept.png and rendered dashboard with image inspection: sidebar/navigation order, navy camera surface and framing, white background/teal actions, three summary columns, session-control hierarchy, outlined enrollment action, empty attendance table. Compact desktop preview height was adjusted after comparison; navigation labels now remain accessible at narrow widths.

Intentional additions beyond concept: visible uncalibrated-threshold notice, disabled start-session button until name entered, model/prototype footer. Actual camera switches to its 4:3 preview proportions. No fake people or metrics. Primary copy retained; real input placeholder names a Deep Learning Lab session.

## Remaining human validation
Run with consenting volunteers on the target webcam; measure false matches/rejections and independent unknown attempts. Calibrate then freeze settings before collecting test sessions. Check latency on target hardware, capture failure rate, varied lighting/angles and photo/replay limitations. Full real-camera enrollment-to-attendance workflow and biometric accuracy remain unverified until that experiment.
