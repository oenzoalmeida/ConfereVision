# Adaptador WSGI para Vercel Functions (@vercel/python). Expõe a aplicação
# Django como callable ASGI/WSGI do runtime serverless, com o caminho do
# projeto no sys.path. O modelo ONNX é embarcado via includeFiles (vercel.json)
# e continua validado por SHA-256 em detector.py.
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
from config.wsgi import application
app = application
