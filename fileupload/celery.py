import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fileupload.settings")

app = Celery("fileupload")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()
