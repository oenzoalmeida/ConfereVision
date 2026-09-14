#!/usr/bin/env bash
set -euo pipefail
python -m pip install -r requirements.txt
python download_model.py
python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py bootstrap_admin
