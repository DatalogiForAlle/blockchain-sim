#!/bin/bash

set -e

echo "${0}: running migrations."
python manage.py migrate

echo "${0}: collecting static files."
python manage.py collectstatic --noinput --clear

echo "${0}: running production server."
pipenv run gunicorn config.wsgi:application --bind 0.0.0.0:8005