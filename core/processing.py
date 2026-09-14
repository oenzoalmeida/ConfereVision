import io,time,tempfile
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageOps,UnidentifiedImageError
from detector import detect_real
from vision import detect,compare,sample

def analyze(frame,kit):
    if kit.mode=='real':annotated,objects=detect_real(frame)
    else:
        annotated,_,objects=detect(frame)
    ok,rows=compare(kit.composition,objects)
    rows=[{'label':r['Classe'],'expected':r['Esperado'],'found':r['Detectado'],'difference':r['Diferença']} for r in rows]
    return ok,rows,cv2.imencode('.jpg',annotated,[cv2.IMWRITE_JPEG_QUALITY,82])[1].tobytes()

def process(data):
    kit=data['kit'];origin=data['source'];upload=data.get('file');timeline=[]
    if origin in ['correct','missing','extra']:
        frame=sample({'correct':'correto','missing':'faltando','extra':'extra'}[origin])
        approved,rows,image=analyze(frame,kit)
        source='Demonstração sintética: '+origin
    elif origin=='image':
        try:
            with Image.open(upload) as im:
                if im.width*im.height>16_000_000:raise ValueError('Imagem muito grande. Limite de 16 megapixels.')
                if im.format not in ['JPEG','PNG']:raise ValueError('Use imagem JPEG ou PNG.')
                frame=cv2.cvtColor(np.array(ImageOps.exif_transpose(im).convert('RGB')),cv2.COLOR_RGB2BGR)
        except (UnidentifiedImageError,OSError,Image.DecompressionBombError) as exc:raise ValueError('Imagem inválida ou corrompida.') from exc
        approved,rows,image=analyze(frame,kit);source=Path(upload.name).name[:200]
    else:
        suffix=Path(upload.name).suffix.lower()
        if suffix not in ['.mp4','.avi','.mov']:raise ValueError('Use vídeo MP4, AVI ou MOV.')
        path=None;cap=None
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix,delete=False) as f:
                path=f.name
                for chunk in upload.chunks():f.write(chunk)
            cap=cv2.VideoCapture(path)
            fps=cap.get(cv2.CAP_PROP_FPS)
            width=cap.get(cv2.CAP_PROP_FRAME_WIDTH);height=cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            if not cap.isOpened() or not np.isfinite(fps) or not 1<=fps<=120:raise ValueError('Não foi possível ler o vídeo ou FPS não suportado (1–120).')
            if width*height>3840*2160:raise ValueError('Resolução de vídeo acima de 4K não suportada.')
            step=max(1,round(fps))
            start=time.monotonic()
            for i in range(int(fps*15)):
                if time.monotonic()-start>65:raise ValueError('Tempo de processamento excedido. Envie um vídeo menor.')
                ok,frame=cap.read()
                if not ok:break
                if i%step:continue
                approved,rows,image=analyze(frame,kit)
                timeline.append({'second':round(i/fps,2),'approved':approved,'count':sum(r['found'] for r in rows)})
            if not timeline:raise ValueError('Nenhum quadro legível.')
            approved=len(timeline)>=3 and all(r['approved'] for r in timeline[-3:])
            source=Path(upload.name).name[:200]
        finally:
            if cap is not None:cap.release()
            if path:Path(path).unlink(missing_ok=True)
    return dict(source=source,approved=approved,details=rows,timeline=timeline,image=image)
