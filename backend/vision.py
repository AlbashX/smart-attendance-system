import base64
import io
import threading
import time
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
from .core import normalize

ROOT = Path(__file__).resolve().parents[1]


class FaceEngine:
    def __init__(self):
        self.lock = threading.Lock()
        self.detector = None
        self.recognizer = None

    def load(self):
        if self.detector is None:
            detector = ROOT/'models/face_detection_yunet_2023mar.onnx'
            recognizer = ROOT/'models/face_recognition_sface_2021dec.onnx'
            if not detector.exists() or not recognizer.exists():
                raise ValueError('Models missing. Run python scripts/download_models.py')
            cv2.setNumThreads(2)
            self.detector = cv2.FaceDetectorYN.create(str(detector), '', (640,480), .9, .3, 5000)
            self.recognizer = cv2.FaceRecognizerSF.create(str(recognizer), '')

    def extract(self, encoded):
        start = time.perf_counter()
        try:
            raw = base64.b64decode(encoded.split(',')[-1], validate=True)
            with Image.open(io.BytesIO(raw)) as im:
                if im.width * im.height > 1920*1080 or min(im.size) < 32:
                    raise ValueError('Image must be between 32 pixels and 1920 x 1080')
                frame = cv2.cvtColor(np.asarray(im.convert('RGB')), cv2.COLOR_RGB2BGR)
        except Exception as e:
            raise ValueError('Invalid image. Send a JPEG/PNG frame up to 1920 x 1080.') from e
        h,w = frame.shape[:2]
        result = dict(face_count=0, box=None, quality=False, reason='No face detected', width=w, height=h)
        with self.lock:
            self.load()
            self.detector.setInputSize((w,h))
            _, faces = self.detector.detect(frame)
            count = 0 if faces is None else len(faces)
            result['face_count'] = count
            if count != 1:
                result['reason'] = 'Only one person should be in frame' if count > 1 else 'No face detected'
            else:
                face = faces[0]
                x,y,fw,fh = [int(t) for t in face[:4]]
                result['box'] = [x,y,fw,fh]
                if min(fw,fh) < 80:
                    result['reason'] = 'Move closer to the camera'
                elif x < 0 or y < 0 or x+fw > w or y+fh > h:
                    result['reason'] = 'Keep your entire face in frame'
                else:
                    crop = frame[y:y+fh,x:x+fw]
                    gray = cv2.cvtColor(cv2.resize(crop,(112,112)), cv2.COLOR_BGR2GRAY)
                    blur = float(cv2.Laplacian(gray,cv2.CV_64F).var())
                    brightness = float(gray.mean())
                    result.update(blur=blur,brightness=brightness)
                    if blur < 35:
                        result['reason'] = 'Hold still; the face is blurry'
                    elif not 40 < brightness < 220:
                        result['reason'] = 'Use even, brighter lighting without backlight'
                    else:
                        aligned = self.recognizer.alignCrop(frame,face)
                        result.update(quality=True,reason='Face quality passed',embedding=normalize(self.recognizer.feature(aligned)).tolist())
        result['latency_ms'] = round((time.perf_counter()-start)*1000,1)
        return result
