import os
from pathlib import Path
import dj_database_url
BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = os.getenv('DEBUG', '1') == '1'
SECRET_KEY = os.getenv('SECRET_KEY', 'local-development-only-not-for-deployment')
if not DEBUG and SECRET_KEY == 'local-development-only-not-for-deployment':
    raise RuntimeError('SECRET_KEY obrigatório em produção.')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver').split(',')
if os.getenv('RENDER_EXTERNAL_HOSTNAME'): ALLOWED_HOSTS.append(os.environ['RENDER_EXTERNAL_HOSTNAME'])
CSRF_TRUSTED_ORIGINS = [f'https://{h}' for h in ALLOWED_HOSTS if h not in ['localhost','127.0.0.1','testserver']]
INSTALLED_APPS = ['django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles','core']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware','whitenoise.middleware.WhiteNoiseMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware','core.middleware.PasswordChangeMiddleware','core.middleware.AdminLoginThrottleMiddleware','django.contrib.messages.middleware.MessageMiddleware','django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[BASE_DIR/'templates'],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION = 'config.wsgi.application'
DATABASES = {'default': dj_database_url.config(default='sqlite:///'+str(BASE_DIR/'local.sqlite3'), conn_max_age=60, conn_health_checks=True)}
if not DEBUG and (not os.getenv('DATABASE_URL') or DATABASES['default']['ENGINE']!='django.db.backends.postgresql'): raise RuntimeError('DATABASE_URL PostgreSQL persistente obrigatório em produção.')
AUTH_PASSWORD_VALIDATORS = [{'NAME':'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},{'NAME':'django.contrib.auth.password_validation.MinimumLengthValidator','OPTIONS':{'min_length':12}},{'NAME':'django.contrib.auth.password_validation.CommonPasswordValidator'},{'NAME':'django.contrib.auth.password_validation.NumericPasswordValidator'}]
LANGUAGE_CODE='pt-br'
TIME_ZONE='America/Sao_Paulo'
USE_I18N=True
USE_TZ=True
STATIC_URL='/static/'
STATIC_ROOT=BASE_DIR/'staticfiles'
STATICFILES_DIRS=[BASE_DIR/'static']
STORAGES={'default':{'BACKEND':'django.core.files.storage.FileSystemStorage'},'staticfiles':{'BACKEND':'whitenoise.storage.CompressedManifestStaticFilesStorage'}}
DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'
LOGIN_URL='/entrar/'
LOGIN_REDIRECT_URL='/'
LOGOUT_REDIRECT_URL='/entrar/'
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SECURE=not DEBUG
CSRF_COOKIE_SECURE=not DEBUG
SESSION_COOKIE_SAMESITE='Lax'
SESSION_COOKIE_AGE=7200
SESSION_EXPIRE_AT_BROWSER_CLOSE=True
SECURE_SSL_REDIRECT=not DEBUG
SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO','https')
SECURE_HSTS_SECONDS=2592000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
X_FRAME_OPTIONS='DENY'
FILE_UPLOAD_MAX_MEMORY_SIZE=2*1024*1024
DATA_UPLOAD_MAX_MEMORY_SIZE=35*1024*1024
DATA_UPLOAD_MAX_NUMBER_FIELDS=150
EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST=os.getenv('EMAIL_HOST','')
EMAIL_PORT=int(os.getenv('EMAIL_PORT','587'))
EMAIL_HOST_USER=os.getenv('EMAIL_HOST_USER','')
EMAIL_HOST_PASSWORD=os.getenv('EMAIL_HOST_PASSWORD','')
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=os.getenv('DEFAULT_FROM_EMAIL','admin@conferevision.invalid')
