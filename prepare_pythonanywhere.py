"""Configura o projeto no PythonAnywhere sem expor segredos ou alterar outros sites."""
import json,os,pwd,secrets,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent
username=pwd.getpwuid(os.getuid()).pw_name
if not str(root).startswith('/home/'+username+'/'):
    raise SystemExit('Execute este preparador dentro da sua pasta /home no PythonAnywhere.')
path=root/'deployment-private.json'
if not path.exists():
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as f:json.dump({'hostname':username+'.pythonanywhere.com','secret_key':secrets.token_urlsafe(64)},f)
configuration=json.loads(path.read_text())
os.environ['DJANGO_SETTINGS_MODULE']='config.pythonanywhere'
for command in [('migrate','--noinput'),('bootstrap_admin',),('collectstatic','--noinput'),('check','--deploy')]:
    subprocess.run([sys.executable,str(root/'manage.py'),*command],cwd=root,check=True)
wsgi=root/'pythonanywhere_wsgi.py'
wsgi.write_text('import os, sys\n'+'sys.path.insert(0, '+repr(str(root))+')\n'+"os.environ['DJANGO_SETTINGS_MODULE']='config.pythonanywhere'\nfrom django.core.wsgi import get_wsgi_application\napplication=get_wsgi_application()\n")
print('Configuração concluída. WSGI gerado em pythonanywhere_wsgi.py. Não alterou outros aplicativos.')
