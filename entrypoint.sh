#!/bin/bash

set -e

echo "${0}: running migrations."
python manage.py reset_db --noinput
#python manage.py flush --no-input
#python manage.py makemigrations --merge --noinput  
python manage.py migrate

echo "${0}: collecting static files."
python manage.py collectstatic --noinput --clear

#echo "${0}: populating test database"
#python manage.py setup_test_data

echo "${0}: Running development server."
python manage.py runserver 0.0.0.0:8000
