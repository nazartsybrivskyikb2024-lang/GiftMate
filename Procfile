release: python manage.py migrate --noinput && python manage.py collectstatic --noinput
web: gunicorn giftmate_project.wsgi:application --workers 3 --bind 0.0.0.0:$PORT
