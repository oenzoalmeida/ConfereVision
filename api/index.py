# Adaptador WSGI para Vercel Functions (@vercel/python). Coleta os estáticos
# em /tmp no cold start (o build do sandbox não compartilha o venv da função)
# e então expõe a aplicação Django. O modelo ONNX segue embarcado via
# includeFiles e validado por SHA-256 em detector.py.
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ.setdefault('STATIC_ROOT', '/tmp/staticfiles')
import django
django.setup()
from django.core.management import call_command
call_command('collectstatic', interactive=False, verbosity=0)
from config.wsgi import application
app = application
