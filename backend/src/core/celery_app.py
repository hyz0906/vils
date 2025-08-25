"""
Celery configuration and task queue
"""

from celery import Celery
from typing import Any

from .config import settings


# Create Celery app
celery_app = Celery(
    "vils",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "src.services.build_tasks",
        "src.services.git_tasks", 
        "src.services.notification_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        "src.services.build_tasks.*": {"queue": "build_queue"},
        "src.services.git_tasks.*": {"queue": "git_queue"},
        "src.services.notification_tasks.*": {"queue": "notification_queue"},
    },
    
    # Task configuration
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    result_expires=3600,
    timezone="UTC",
    enable_utc=True,
    
    # Worker configuration
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    
    # Queue configuration
    task_default_queue="default",
    task_create_missing_queues=True,
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Retry configuration
    task_annotations={
        "*": {"rate_limit": "10/s"},
        "src.services.build_tasks.run_build": {"rate_limit": "5/s"},
    },
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "cleanup_old_tasks": {
            "task": "src.services.notification_tasks.cleanup_old_notifications",
            "schedule": 3600.0,  # Every hour
        },
        "health_check": {
            "task": "src.services.build_tasks.health_check",
            "schedule": 300.0,  # Every 5 minutes
        },
    },
)


@celery_app.task(bind=True)
def debug_task(self) -> str:
    """Debug task for testing Celery"""
    return f"Request: {self.request!r}"


def create_celery_app() -> Celery:
    """Create and configure Celery app"""
    return celery_app