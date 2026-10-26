# Deep learning training and evaluation plan

Reviewed 26 October 2026. This plan incorporates the latest requested scope. It supersedes earlier proposals requiring three separate attendance windows or a wall-mounted camera for the current prototype. These are proposed changes, not implemented capabilities.

## Current code findings

- `backend/vision.py` uses pretrained YuNet and SFace for single-face detection and embedding extraction. These weights are not trained by this project.
- Accepted enrollment samples already have normalized embeddings; the store retains samples and a centroid. Enrollment and threshold calibration are not neural-network training.
- Current recognition has no presentation attack detector. A clear phone photograph can pass identity and quality checks. Repeated identity matches do not establish liveness.
- The Accuracy Lab collects labeled validation/test camera attempts and reports recognition, unknown rejection, pairwise FAR/FRR and extraction latency. It does not train a network, evaluate recorded-video liveness, or retain versioned training runs. Quality-rejected captures are excluded from its current metrics.
- The detector currently rejects multiple faces. Whole-class simultaneous attendance is not an existing capability.

## Proposed learning task

Keep YuNet/SFace as the pretrained identity baseline. Train a MobileNetV3-Small live/spoof classifier: replace its classifier with two outputs, train the head, then fine-tune final convolutional blocks. Compare against a small CNN trained from scratch using identical data splits. Train with cross-entropy, Adam, training-only augmentation, validation early stopping and saved checkpoints. Record which layers were trainable, parameter counts, epoch losses, validation scores, seed and software versions.

This supplies a genuine supervised deep-learning experiment with forward passes, loss computation, backpropagation and optimization. Training SFace from scratch on one student or a small class is not justified. If the course requires training the identity network specifically, agree that additional scope with the supervisor; PAD training is a proposed substantive DL contribution.

## Collection and splitting

Target 12–20 consenting adult participants, with at least three recording sessions each. This is a feasibility target, not a sufficient dataset for deployment claims. Capture real live faces, printed photographs, phone-displayed photographs and screen video replays using varied lighting, backgrounds and devices. Keep attack subtype and source identity labels. Capture both live and attack samples with the same cameras/backgrounds so the classifier cannot simply learn device or room differences.

Maintain a manifest with sample ID, participant pseudonym, source clip ID, session, camera/device, live/spoof label, attack subtype, consent reference, split and file hash. Do not expose names in experiment exports by default. Keep originals locally only for the agreed training retention period; delete temporary upload files. Dataset enrollment is distinct from roster import and requires explicit consent.

For PAD, allocate approximately 60/20/20% of participants to train/validation/test before frame extraction. All recordings of one participant stay in one split. Keep source media and derived images together, audit duplicates, and include an unseen-device test when feasible. With very few participants, use grouped cross-validation and disclose high uncertainty rather than treating thousands of adjacent frames as independent observations.

Recognition needs enrolled identities in both gallery and probe tests: separate these by recording session, not identity. Unknown identities must be excluded from the gallery; use different unknown participants in validation and test. LFW is an optional separate verification benchmark, not a live/spoof training dataset. Follow its official protocol if claiming an LFW result.

Each accepted enrollment image receives its own normalized SFace embedding and source/sample identifier. Retain individual embeddings as well as any centroid. Reject unusable images explicitly instead of embedding bad crops. Recorded test frames can be embedded transiently; storing every camera frame permanently is unnecessary.

## Runtime decisions

1. Start the laptop/mobile camera and identify the current scheduled class.
2. Detect and track a face; apply quality checks. Bind identity and PAD decisions to the same face track and recent frame sequence.
3. Compute its identity embedding and match against the gallery with locked threshold and ambiguity margin.
4. Run the trained PAD network and aggregate a short sequence with validation-selected rules. A short confirmation sequence counts as one verified sighting, not three attendance windows.
5. Known identity plus a live decision marks present once per session. Unknown identities never mark attendance. Suspected photo/replay or inconclusive decisions produce a review event and do not mark present.
6. At session end, finalize remaining eligible students as absent with teacher correction available. Recognition failure must remain distinguishable from verified absence in the review workflow.

A missing, failed or unvalidated PAD model must not silently authorize attendance. Label the existing path as an identity-only demonstration until the gate is ready. A random head-turn challenge can be an additional supervised fallback; simple blink detection alone does not prevent video replay. Passive RGB PAD cannot guarantee rejection of every attack. Flags indicate suspected presentation attacks, not proof of student misconduct.

Photo/video upload is for consented enrollment or labeled offline evaluation. Uploaded media must never be treated as a live attendance camera source.

## Accuracy Lab design

Use four views: Dataset, Training runs, Test runs and Recorded-video evaluation.

Training runs show architecture, frozen/trainable layers, dataset version and counts, split audit, seed, hyperparameters, epoch loss/accuracy curves, selected checkpoint and elapsed training time. Preserve failed runs and error messages.

Test runs show identity recognition accuracy, unknown rejection, verification FAR/FRR, PAD confusion matrix, precision/recall/F1 with the positive class stated, APCER (attacks classified live), BPCER (live presentations classified attack), and per-attack results. Report raw numerator/denominator counts and uncertainty alongside percentages. Report acquisition failures and inconclusive cases separately; do not inflate accuracy by dropping them silently.

Also report end-to-end attack attendance acceptance, successful live attendance, median/p95 inference latency, full decision latency and processing FPS on named hardware. Recognition similarity and PAD confidence are scores, not accuracy percentages.

Recorded-video evaluation accepts a consented clip plus ground truth: who appears, whether the presentation is live or an attack, attack subtype and time intervals. Run the same detector, identity, PAD and temporal logic as the camera, in an isolated evaluation context that cannot write real attendance. Distinguish per-frame, per-track and per-clip results. A recording without labels can show predictions and timings, but cannot yield accuracy.

Store immutable run IDs, timestamps, checkpoint hashes, dataset-manifest hashes, threshold values, metric definitions, denominators, predictions and JSON/CSV exports. Calibration uses validation only; final testing does not modify thresholds. Changing model weights, gallery or preprocessing requires a new evaluation run. Show “Not evaluated” until real labeled tests exist.

## Implementation order and acceptance checks

1. Dataset manifest, consent and split-validation tooling. Reject duplicated source clips across splits.
2. Reproducible training/evaluation scripts and checkpoint metadata. Verify the loss backpropagates and trainable weights change; smoke tests are not evidence of useful accuracy.
3. PAD inference and face-track gate. Test that phone-photo/replay predictions, unknowns, missing models and inference failures cannot create attendance.
4. Versioned experiment storage and Accuracy Lab views. Verify exported metrics match labeled fixture predictions, including zero-denominator cases.
5. Isolated recorded-video evaluation. Verify it never creates live attendance and reports every labeled attempt.
6. Held-out real/live/photo/replay trials on prototype hardware. Compare the original baseline and trained alternatives; publish actual results, limitations and failure examples.

Keep existing student, timetable and attendance changes. Use D1/D2/D3, omit MDM, retain the supplied teacher corrections and store email rather than phone/CGPA. Front-wall whole-class monitoring remains future work.

## Proposal status

The accompanying Word proposal fills the supplied RBU template with the four team members. It describes planned training and evaluation, not completed research results. The template limits the proposal to three pages; this is stricter than the PDF's four-page limit. A final experimental report needs the actual dataset counts, trained checkpoints, test results and plots after experiments.

Sources: OpenCV face detection/recognition tutorial (https://docs.opencv.org/4.x/d0/dd4/tutorial_dnn_face.html); PyTorch transfer learning tutorial (https://docs.pytorch.org/tutorials/beginner/transfer_learning_tutorial); NISTIR 8491 (https://doi.org/10.6028/NIST.IR.8491).
