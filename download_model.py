"""Baixa peso oficial OpenCV Zoo e confere o SHA-256 fixado neste arquivo."""
import hashlib,urllib.request
from pathlib import Path
URL='https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/object_detection_yolox/object_detection_yolox_2022nov.onnx'
SHA='c5c2d13e59ae883e6af3b45daea64af4833a4951c92d116ec270d9ddbe998063'
def main():
    path=Path(__file__).resolve().parent/'models'/'yolox.onnx'
    if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()==SHA:
        print('Modelo já validado.');return
    path.parent.mkdir(exist_ok=True)
    tmp=path.with_suffix('.download')
    try:
        with urllib.request.urlopen(URL,timeout=120) as response,tmp.open('wb') as target:
            while chunk:=response.read(1024*1024):target.write(chunk)
        if hashlib.sha256(tmp.read_bytes()).hexdigest()!=SHA:raise RuntimeError('Hash do modelo divergente; download rejeitado.')
        tmp.replace(path)
        print('Modelo YOLOX baixado e hash SHA-256 validado.')
    finally:tmp.unlink(missing_ok=True)
if __name__=='__main__':main()
