
import os
from celery import Celery

# set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oumraa.settings')

app = Celery('oumraa')

# load settings from Django settings.py, namespace CELERY
app.config_from_object('django.conf:settings', namespace='CELERY')

# auto-discover tasks in all installed apps
app.autodiscover_tasks()
