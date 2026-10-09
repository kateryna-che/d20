#!/usr/bin/env bash
# Exit on error
set -o errexit

# manage.py works with the development settings unless it is told otherwise.
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-d20_dev.settings.prod}"

pip install -r requirements.txt

# Collect the static files for WhiteNoise
python manage.py collectstatic --no-input

# Apply any outstanding database migrations
python manage.py migrate
