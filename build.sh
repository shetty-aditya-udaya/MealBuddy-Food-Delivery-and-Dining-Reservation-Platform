#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

echo "=== Installing Dependencies ==="
pip install -r requirements.txt

echo "=== Collecting Static Assets ==="
python manage.py collectstatic --noinput

echo "=== Applying Database Migrations ==="
python manage.py migrate
