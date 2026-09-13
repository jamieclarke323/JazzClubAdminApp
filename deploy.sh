#!/usr/bin/env bash
# Run this after `git pull` on the server to bring the deployed app up to date.
# Usage: bash deploy.sh
set -e
cd "$(dirname "$0")"

source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput

echo "Done. Reload the web app from the PythonAnywhere 'Web' tab (or run: touch /var/www/<your-username>_pythonanywhere_com_wsgi.py)."
