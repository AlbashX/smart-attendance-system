"""Framework-neutral logger for real epoch values and independent evaluation trials."""
import json
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.lab import Run, Epoch, ModelInfo, Trial


class MetricsLogger:
    def __init__(self, class_id, student_id, name, model, training_images, validation_images):
        self.run=Run(class_id=class_id,student_id=student_id,name=name,model=ModelInfo(**model),
                     counts={'training_images':training_images,'validation_images':validation_images})

    def log_epoch(self,epoch,train_accuracy,validation_accuracy,train_loss,validation_loss):
        self.run.history.append(Epoch(epoch=epoch,train_accuracy=train_accuracy,
            validation_accuracy=validation_accuracy,train_loss=train_loss,validation_loss=validation_loss))

    def log_trial(self,actual_positive,predicted_positive,similarity):
        self.run.trials.append(Trial(actual_positive=actual_positive,
                                    predicted_positive=predicted_positive,similarity=similarity))

    def save(self,path,training_seconds=None,threshold=.45,notes=''):
        self.run.model.training_seconds=training_seconds
        self.run.threshold=threshold
        self.run.notes=notes
        # Revalidate the full payload before writing. No predictions or history are invented.
        validated=Run.model_validate(self.run.model_dump())
        target=Path(path)
        target.parent.mkdir(parents=True,exist_ok=True)
        temporary=target.with_suffix(target.suffix+'.tmp')
        temporary.write_text(json.dumps(validated.model_dump(),indent=2,allow_nan=False),encoding='utf-8')
        temporary.replace(target)
        return target
