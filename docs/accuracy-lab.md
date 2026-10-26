# Accuracy Lab

Open Accuracy lab, choose a class, then a student. The second dropdown follows the timetable batch (for example D3 for a D3 lab). All classes includes the whole roster. Repeated weekly occurrences of the same course/batch share one class selector. The dashboard shows epoch accuracy/loss, final KPIs, one-versus-rest evaluation, confusion matrix, cosine statistics, ROC when both classes exist, counts and model metadata.

Expand **Collect real evaluation attempts** to capture validation/test observations and view the existing aggregate recognition accuracy, unknown-person rejection, latency and JSON export. These probes are separate from imported training runs.

## Sources and interpretation

- **Recorded results** loads the latest saved run for that exact class/student, or current held-out recognition probes if no saved run exists. Select an older saved run from Model run. Training history belongs to the model run, not a separate network trained for each student.
- **Demo data (synthetic)** is an explicit preview. Its banner and JSON export identify it as synthetic. No example is inserted into your database. Real enrollment and attendance counts remain labeled separately. Demo values are not evidence of accuracy, PAD or training.
- Empty real data displays dashes / Not recorded, never synthetic replacements. Frozen SFace inference has no project training epochs or optimizer. Enrollment images are not training images.
- Existing probes lack class labels, so their evaluation explicitly spans all classes. Saved imported runs are keyed to the selected class and student. Attendance counts include present and absent records in the selected course/batch.
- Precision, recall and F1 use the selected student as the positive class. Confusion rows are actual labels; columns are predicted labels. FAR = FP/(FP+TN), FRR = FN/(FN+TP). Undefined denominators return null. Scores are cosine similarity, not confidence probabilities. Distance = 1 - similarity. ROC sweeps similarity only and may differ from decisions using an ambiguity margin. Counts are attempt counts, not independent-person counts.
- The class detail table shows each student's latest available real evaluation and its source. Different runs are not pooled into a claimed class accuracy.

## API

All routes use the existing same-origin and local gateway controls.

```
GET  /api/lab/classes
GET  /api/lab/classes/{class_id}/students
GET  /api/lab/classes/{class_id}/students/{student_id}/runs
GET  /api/lab/classes/{class_id}/students/{student_id}/metrics
GET  /api/lab/classes/{class_id}/students/{student_id}/metrics?run_id={id}
GET  /api/lab/classes/{class_id}/students/{student_id}/metrics?source=demo
GET  /api/lab/classes/{class_id}/summary
POST /api/lab/runs
```

POST validates finite values, probability ranges, ordered epoch numbers and class membership. It creates a new immutable run ID in SQLite's model_runs table. This is additive and does not reset existing students or attendance. Deleting a student deletes their saved runs. Probe reset does not delete saved model runs. Saved runs describe the checkpoint/gallery used for that experiment, not necessarily the current deployed state. Importing metrics does not deploy model weights.

## Logging real training

There is no actual project-specific neural training loop in the current application. `scripts/log_training_metrics.py` is a logger to integrate into your future Keras/PyTorch training job. Do not create epoch curves from centroid similarity.

Example using an actual Keras History returned by `model.fit`:

```python
from scripts.log_training_metrics import MetricsLogger
import time

logger = MetricsLogger(
    class_id=selected_class_id, student_id=selected_student_id,
    name="Recognition experiment 1",
    model={"architecture": model.name, "embedding_size": embedding_dimension,
           "optimizer": "Adam", "learning_rate": learning_rate,
           "batch_size": batch_size, "checkpoint": checkpoint_hash,
           "dataset_version": manifest_hash},
    training_images=len(train_images), validation_images=len(validation_images))

started = time.perf_counter()
history = model.fit(train_images, train_labels, validation_data=(validation_images, validation_labels),
                    epochs=epochs, batch_size=batch_size).history
for i in range(len(history["loss"])):
    logger.log_epoch(i+1, history["accuracy"][i], history["val_accuracy"][i],
                     history["loss"][i], history["val_loss"][i])
training_seconds = time.perf_counter() - started

# Run inference on separate labeled test captures. These must be genuine independent observations.
# cosine_scores and predicted_student_ids come from the actual recognition pipeline.
for actual_id, predicted_id, cosine_score in zip(test_student_ids, predicted_student_ids, cosine_scores):
    logger.log_trial(actual_id == selected_student_id,
                     predicted_id == selected_student_id, float(cosine_score))

logger.save("data/experiments/recognition-run.json", training_seconds,
            threshold=locked_threshold,
            notes="Separate capture sessions; thresholds selected only on validation.")
```

Compile the Keras model with an accuracy metric before fit. Adapt metric key names if your model uses named outputs. For PyTorch, call `log_epoch` after each epoch with actual correct/total fractions and sample-weighted mean losses from the train/validation loaders; call `log_trial` only on the independent evaluation set. Supply optimizer settings from the real run, not this illustrative configuration. Install a training framework only when starting that training workflow.

Select the matching class/student in Accuracy Lab and use **Import run** to upload the JSON; alternatively POST that JSON to `/api/lab/runs`. Get the IDs from the class/student GET endpoints. The import JSON schema is defined by `Run` in backend/lab.py. Export report downloads a calculated report with provenance; it is intentionally different from the raw training import schema.

PAD training is a different binary task: live versus spoof. Do not label its F1 or APCER as student recognition F1/FAR. This dashboard's evaluation import expects identity ground truth and cosine scores. Extend the schema with an explicit PAD task before reporting PAD evaluation here.

## Verification and local development

`python -m pytest tests -q` checks metrics, empty states, explicit demos, persistence, class membership, origin protection and existing attendance behavior. `npm --prefix frontend run build` produces the locally hosted UI. Vite preserves Host and Origin when proxying API calls, so legitimate same-origin requests pass without allowing unrelated origins. Local builds use `/`; GitHub Pages builds opt into the repository base path. GitHub Pages remains a static frontend and cannot run the Python API.

Chart implementation follows the Chart.js responsive container and lifecycle APIs:
https://www.chartjs.org/docs/latest/configuration/responsive.html
https://www.chartjs.org/docs/latest/developers/api.html
