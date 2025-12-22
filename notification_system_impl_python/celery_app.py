from celery import Celery
from celery.schedules import crontab
import os
from dotenv import load_dotenv

load_dotenv()

celery_app = Celery(
    'notification_system',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    include=['workers.tasks']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=240,
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

celery_app.conf.beat_schedule = {
    'process-retry-queue': {
        'task': 'workers.tasks.process_retry_queue',
        'schedule': 60.0,
    },
    'cleanup-old-retries': {
        'task': 'workers.tasks.cleanup_old_retries',
        'schedule': crontab(hour=2, minute=0),
    },
    'process-dlq': {
        'task': 'workers.tasks.process_dlq_notifications',
        'schedule': 300.0,
    },
}

if __name__ == '__main__':
    celery_app.start()
