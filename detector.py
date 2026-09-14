"""YOLOX via OpenCV DNN. Decodificação baseada no OpenCV Zoo (Apache 2.0)."""
from pathlib import Path
from threading import Lock
import cv2
import numpy as np
cv2.setNumThreads(1)
PRODUCTS={24:'Mochila',25:'Guarda-chuva',26:'Bolsa',27:'Gravata',28:'Mala',39:'Garrafa',40:'Taça',41:'Caneca / xícara',42:'Garfo',43:'Faca',44:'Colher',45:'Tigela',46:'Banana',47:'Maçã',49:'Laranja',63:'Notebook',64:'Mouse',65:'Controle remoto',66:'Teclado',67:'Celular',73:'Livro',74:'Relógio',75:'Vaso',76:'Tesoura',77:'Urso de pelúcia',79:'Escova de dentes'}
_LOCK=Lock()
_NET=None

def detect_real(frame,threshold=.45):
    global _NET
    if frame is None or not frame.size:raise ValueError('Imagem inválida.')
    scale=min(1,1200/max(frame.shape[:2]))
    frame=cv2.resize(frame,None,fx=scale,fy=scale)
    ratio=min(640/frame.shape[0],640/frame.shape[1])
    resized=cv2.resize(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB),(int(frame.shape[1]*ratio),int(frame.shape[0]*ratio)))
    padded=np.full((640,640,3),114,np.float32)
    padded[:resized.shape[0],:resized.shape[1]]=resized
    blob=padded.transpose(2,0,1)[None]
    path=Path(__file__).resolve().parent/'models'/'yolox.onnx'
    if not path.exists():raise RuntimeError('Modelo não instalado. Execute python download_model.py no servidor.')
    with _LOCK:
        if _NET is None:_NET=cv2.dnn.readNet(str(path))
        _NET.setInput(blob)
        dets=_NET.forward()[0].copy()
    grids=[];strides=[]
    for stride in (8,16,32):
        y,x=np.mgrid[:640//stride,:640//stride]
        grid=np.stack([x,y],axis=-1).reshape(-1,2)
        grids.append(grid);strides.append(np.full((len(grid),1),stride))
    grid=np.concatenate(grids);stride=np.concatenate(strides)
    dets[:,:2]=(dets[:,:2]+grid)*stride
    dets[:,2:4]=np.exp(dets[:,2:4])*stride
    boxes=dets[:,:4].copy()
    boxes[:,:2]-=boxes[:,2:4]/2
    scores=dets[:,4:5]*dets[:,5:]
    class_ids=np.argmax(scores,axis=1)
    conf=np.max(scores,axis=1)
    keep=cv2.dnn.NMSBoxesBatched(boxes.tolist(),conf.tolist(),class_ids.tolist(),threshold,.5)
    annotated=frame.copy();objects=[]
    for i in np.array(keep).flatten():
        cls=int(class_ids[i])
        # Pessoas e móveis são contexto. Todo objeto detectado do catálogo entra na conferência, inclusive excedentes.
        if cls not in PRODUCTS:continue
        box=boxes[i]/ratio
        x,y,w,h=[int(v) for v in box]
        x1=max(0,x);y1=max(0,y);x2=min(frame.shape[1]-1,x+w);y2=min(frame.shape[0]-1,y+h)
        if x2<=x1 or y2<=y1:continue
        label=PRODUCTS[cls]
        objects.append({'classe':label,'confidence':round(float(conf[i]),3),'caixa':[x1,y1,x2-x1,y2-y1]})
        cv2.rectangle(annotated,(x1,y1),(x2,y2),(115,170,15),2)
        text=f'{label} {conf[i]:.0%}'.encode('ascii','ignore').decode()
        cv2.putText(annotated,text,(x1,max(20,y1-8)),cv2.FONT_HERSHEY_SIMPLEX,.55,(90,90,10),2)
    return annotated,objects
