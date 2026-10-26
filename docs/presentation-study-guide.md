# Proposal and presentation explanation

## The main statement to use in your viva

“We have implemented a local attendance prototype using pretrained YuNet and SFace. Each accepted enrollment image produces a normalized face embedding. Our proposed training contribution is a lightweight CNN that distinguishes live faces from photo and replay attacks. We will evaluate recognition and spoof detection separately, then evaluate the combined attendance decision.”

Do not say the team has already trained a spoof detector or achieved the figures in the original presentation. The reviewed code does not contain that training pipeline or its results.

## What each model does

**YuNet detects the face.** It predicts a face bounding box and facial landmarks. Landmarks allow alignment so the eyes and other features occupy consistent positions in the crop. The downloaded YuNet ONNX model already has learned weights. OpenCV executes it.

**SFace creates the embedding.** The pretrained network converts an aligned face image into a vector of 128 numerical values. These are learned identity features, not named measurements such as eye width or nose length. Our code normalizes the vector to unit length. Different good images of the same person should produce nearby vectors, but lighting, pose and poor quality still affect recognition.

**The gallery stores enrollment information.** Each accepted image contributes an embedding. The current app also calculates a normalized mean vector, called a centroid, for each student. During recognition it compares the new embedding with student centroids using cosine similarity. Higher similarity means greater vector alignment. A score is not a calibrated probability or an accuracy percentage. Reject a low score or an ambiguous match. Enrollment and selecting a similarity threshold do not train the network.

**MobileNetV3-Small is the proposed trainable spoof detector.** Start with ImageNet-pretrained weights, replace the final classifier with two outputs, and train on labeled live/spoof crops. First train the new head, then fine-tune final feature blocks. This is transfer learning. ImageNet supplies initial visual features; it does not make the network a ready-made liveness detector.

## How actual training works

1. Collect consenting live recordings and attack presentations: printed photos, phone-displayed photos and replay videos. Target 12–20 adults with multiple sessions, subject to actual participation. Label source identity, live/spoof class, attack subtype, session and device.
2. Split PAD participants approximately 60% training, 20% validation and 20% test. Keep a participant and all their source clips within one split. Extract frames only after assignment. Otherwise adjacent frames can leak across splits and create misleading accuracy.
3. Run a batch of training images through the CNN. Cross-entropy measures error against the labels. Backpropagation computes gradients. Adam updates the trainable weights. An epoch is one pass through the training set.
4. Use validation loss and metrics to select a checkpoint, stop training and choose decision thresholds. Proposed starting learning rates are 0.001 for the head and 0.0001 for fine-tuning, not proven optimal settings.
5. Freeze the chosen model and thresholds. Evaluate the test set without further tuning. Compare against a small CNN trained from scratch using the same splits, and compare attendance with the current no-PAD baseline.

Recognition uses a different split logic: enrolled identities must also appear in the known probe set, but enrollment and test captures come from separate sessions. Unknown test identities never appear in the gallery. LFW supplies a separate identity-verification benchmark; it does not contain the required live/spoof labels.

## Why a mobile photo currently passes

The photo still shows the enrolled person's facial identity features. The existing system can match those features even though the person is absent. Sharpness checks and repeated matches do not establish liveness. A separately trained and evaluated presentation attack detector is needed. No RGB method guarantees rejection of every spoof, so retain unknown/inconclusive states and teacher review.

## Explanation of the nine proposal sections

| Section | What you should explain |
|---|---|
| Problem and motivation | Manual attendance and proxy risks motivate the prototype. Your phone-photo failure reveals a missing live/spoof check. |
| Objectives | Extract identity embeddings, train a spoof CNN, evaluate both tasks and integrate verified attendance. These are measurable objectives rather than claimed results. |
| Dataset | Use consenting local enrollment and live/attack recordings. Dataset counts are targets until collection finishes. LFW is optional verification evidence. |
| Methodology | Detection/alignment supplies crops to identity recognition and live/spoof classification. The final decision combines both outputs. |
| Experimental plan | Explain training/validation/test separation, cross-entropy, Adam, model comparison and metric definitions. |
| Expected deliverables | Working local application, trained checkpoint, manifest, learning curves, test reports and demo. These become completed deliverables only after implementation. |
| Work distribution | Srujal: consent/data; Sujal: CNN experiments; Syed Albash: recognition/integration; Tanmay: Accuracy Lab/report. These are proposed responsibilities and everyone should understand the full pipeline. |
| Timeline | Scope, collection, training, integration, held-out tests and demonstration. No fabricated calendar dates or completed phases. |
| References | OpenCV explains pretrained recognition, PyTorch explains transfer learning, and NIST explains presentation attack evaluation. |

The supplied Word file is a **proposal**. A final experimental report will additionally need actual dataset counts, training configuration, curves, held-out results, failure examples and limitations.

## Presentation speaking guide

1. **Introduction:** State the project, members, current pretrained recognition and proposed trained spoof detector.
2. **Problem and scope:** Describe manual attendance and the observed mobile-photo false attendance. Limit the present prototype to consenting students and a laptop/mobile camera.
3. **Objectives:** Explain what will be built and measured. One verified live sighting gives one attendance entry for a class.
4. **Models:** Name YuNet, SFace, cosine matching, proposed MobileNetV3-Small and the React/FastAPI/SQLite application. Avoid the original Haar/FaceNet512/pickle description.
5. **Training:** Explain labels, participant splits, transfer learning, loss, optimizer and the separate test set. These experiments are planned.
6. **Embeddings:** Walk through an image becoming a 128-value vector and then a cosine match. Enrollment stores examples; it does not optimize model weights.
7. **Privacy:** Obtain consent and protect embeddings. Phone frames travel to the laptop. Uploaded video uses temporary files. Training media requires controlled retention. Do not claim embeddings are irreversible.
8. **Evaluation:** Present metric definitions and show actual numbers only when recorded. Accuracy needs ground-truth labels. An uploaded unlabelled video gives predictions, not measurable accuracy.
9. **Integration:** The future gate needs a known identity and live decision for the same face track. Suspected attacks do not mark present. Whole-class/depth-camera deployment is future work.
10. **Conclusion:** Restate existing capabilities, the planned DL contribution and the next experiment. Do not claim proxy attendance has been eliminated.

## Metrics to understand

- Recognition accuracy: correctly identified known attempts divided by all known attempts, including rejected known attempts in the denominator.
- Verification FAR: impostor comparisons accepted as matches divided by impostor comparisons.
- Verification FRR: genuine comparisons rejected divided by genuine comparisons. It is not generally 100% minus overall accuracy.
- Unknown rejection: unknown-person attempts correctly rejected divided by unknown-person attempts.
- APCER: attack presentations wrongly classified as live divided by attack presentations.
- BPCER: real live presentations wrongly classified as attacks divided by real live presentations.
- Precision, recall and F1: report which class is positive and show the confusion matrix and counts.
- End-to-end attack acceptance: attack attempts that actually cause attendance to be marked divided by attack attempts.
- Latency: report median and 95th percentile, separately for inference and the full attendance decision, with the hardware named.

Tiny samples or many neighboring frames cannot substantiate population-wide claims. Preserve source-clip grouping and show counts, conditions and uncertainty.

## Sources

- OpenCV: https://docs.opencv.org/4.x/d0/dd4/tutorial_dnn_face.html
- PyTorch transfer learning: https://docs.pytorch.org/tutorials/beginner/transfer_learning_tutorial
- NIST presentation attack detection: https://doi.org/10.6028/NIST.IR.8491
- Current project code: backend/vision.py, backend/core.py, backend/main.py and backend/store.py.
