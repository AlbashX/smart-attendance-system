"""Download only the two official OpenCV Zoo pretrained ONNX weights."""
from pathlib import Path
import hashlib
import json
import urllib.request

ROOT = Path(__file__).resolve().parents[1] / 'models'
MODELS = {
    'face_detection_yunet_2023mar.onnx': 'face_detection_yunet',
    'face_recognition_sface_2021dec.onnx': 'face_recognition_sface',
}

if __name__ == '__main__':
    ROOT.mkdir(exist_ok=True)
    manifest = {}
    for filename, folder in MODELS.items():
        url = f'https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/{folder}/{filename}'
        path = ROOT / filename
        if not path.exists():
            print(f'Downloading {filename}', flush=True)
            tmp = path.with_suffix('.part')
            urllib.request.urlretrieve(url, tmp)
            if tmp.stat().st_size < 100000: raise RuntimeError('Downloaded file is not a model')
            tmp.replace(path)
        manifest[filename] = {'source': url, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    (ROOT / 'manifest.json').write_text(json.dumps(manifest,indent=2))
    print('Models ready. Source and checksums saved to models/manifest.json.')
