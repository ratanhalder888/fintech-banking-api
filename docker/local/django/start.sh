#!/bin/bash

set -o errexit

set -o pipefail

set -o nounset

python manage.py migrate --no-input --fake-initial || {
    python manage.py migrate django_celery_beat --fake --no-input
    python manage.py migrate --no-input --fake-initial
}
python manage.py collectstatic --no-input

exec python manage.py runserver 0.0.0.0:8000