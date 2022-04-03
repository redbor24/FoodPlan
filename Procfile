release: python manage.py migrate --noinput
web: gunicorn --bind :$PORT --workers 4 --worker-class uvicorn.workers.UvicornWorker dtb.asgi:application
worker: python run_pooling.py