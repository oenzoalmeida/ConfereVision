@echo off
cd /d "%~dp0"
if not exist .venv python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
if errorlevel 1 goto error
python download_model.py
if errorlevel 1 goto error
python manage.py migrate --noinput
if errorlevel 1 goto error
python manage.py bootstrap_admin
if errorlevel 1 goto error
python manage.py collectstatic --noinput
if errorlevel 1 goto error
start http://127.0.0.1:8000
python manage.py runserver 127.0.0.1:8000
pause
exit /b 0
:error
pause
exit /b 1
