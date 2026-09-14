"""Configuração para disco persistente PythonAnywhere; não usar em Render."""
import json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
PRIVATE=ROOT/'deployment-private.json'
if not PRIVATE.exists():raise RuntimeError('Execute python prepare_pythonanywhere.py antes de iniciar.')
configuration=json.loads(PRIVATE.read_text())
os.environ.update(DEBUG='0',SECRET_KEY=configuration['secret_key'],ALLOWED_HOSTS=configuration['hostname'],DATABASE_URL='sqlite:///'+str(ROOT/'local.sqlite3'),PERSISTENT_SQLITE='1')
from .settings import *
DATABASES['default']['OPTIONS']={'timeout':20}
