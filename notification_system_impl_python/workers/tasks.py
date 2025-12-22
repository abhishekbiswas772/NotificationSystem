from celery_app import celery_app
from configs.db import db
from configs.redis import get_redis_pool
from handlers.notification_handler import NotificationHandler
from handlers.notification_provider_handler import NotificationHandler as ProviderHandler
from handlers.retry_handlers import RetryHandler
from handlers.dlq_handler import DLQHandler
from models.notification import Notification
from helpers.enums import NotificationStatus
from helpers.helpers import now_ms
import json
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name='workers.tasks.send_notification', bind=True, max_retries=3)
def send_notification(self, notification_id: str):
    """
    Send a single notification using the appropriate provider

    Args:
        notification_id: ID of the notification to send
    """
    try:
        logger.info(f"Processing notification {notification_id}")

        notification = Notification.query.filter_by(id=notification_id).first()

        if not notification:
            logger.error(f"Notification {notification_id} not found")
            return {'status': 'error', 'message': 'notification not found'}

        if notification.status in [NotificationStatus.SENT, NotificationStatus.CANCELLED]:
            logger.info(f"Notification {notification_id} already {notification.status.value}")
            return {'status': 'skipped', 'message': f'already {notification.status.value}'}

        notification.attempt_count += 1
        notification.last_attempted = now_ms()
        db.session.commit()

        provider_handler = ProviderHandler()
        result = provider_handler.send_notification(notification)

        if result.get('success'):
            notification.status = NotificationStatus.SENT
            notification.sent_at = now_ms()
            notification.provider_response = json.dumps(result.get('response', {}))
            db.session.commit()

            logger.info(f"Notification {notification_id} sent successfully")
            return {'status': 'success', 'notification_id': notification_id}

        else:
            error_message = result.get('message', 'Unknown error')
            logger.error(f"Notification {notification_id} failed: {error_message}")

            retry_handler = RetryHandler()
            retry_handler.schedule_retry(
                notification_id=notification_id,
                attempts=notification.attempt_count,
                error_message=error_message
            )

            return {'status': 'failed', 'message': error_message, 'will_retry': True}

    except Exception as e:
        logger.error(f"Error processing notification {notification_id}: {str(e)}")
        db.session.rollback()

        try:
            raise self.retry(exc=e, countdown=60)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for notification {notification_id}")
            return {'status': 'error', 'message': str(e)}


@celery_app.task(name='workers.tasks.consume_notification_queue')
def consume_notification_queue():
    """
    Consume notifications from Redis queue and dispatch to workers
    """
    try:
        redis_client = get_redis_pool()
        processed = 0

        while True:
            item = redis_client.brpop('notification:queue', timeout=1)

            if not item:
                break

            _, payload = item
            data = json.loads(payload)
            notification_id = data.get('id')

            if notification_id:
                send_notification.delay(notification_id)
                processed += 1

            if processed >= 100:
                break

        logger.info(f"Dispatched {processed} notifications to workers")
        return {'processed': processed}

    except Exception as e:
        logger.error(f"Error consuming queue: {str(e)}")
        return {'error': str(e)}


@celery_app.task(name='workers.tasks.process_retry_queue')
def process_retry_queue():
    """
    Process notifications due for retry
    Runs periodically (every 60 seconds)
    """
    try:
        retry_handler = RetryHandler()
        processed = retry_handler.process_due_retries()

        logger.info(f"Processed {processed} retry notifications")
        return {'processed': processed}

    except Exception as e:
        logger.error(f"Error processing retries: {str(e)}")
        return {'error': str(e)}


@celery_app.task(name='workers.tasks.cleanup_old_retries')
def cleanup_old_retries():
    """
    Cleanup old retry records from Redis
    Runs daily at 2 AM
    """
    try:
        retry_handler = RetryHandler()
        retry_handler.clean_old_retry()

        logger.info("Cleaned up old retry records")
        return {'status': 'success'}

    except Exception as e:
        logger.error(f"Error cleaning up retries: {str(e)}")
        return {'error': str(e)}


@celery_app.task(name='workers.tasks.process_dlq_notifications')
def process_dlq_notifications():
    """
    Check and report on DLQ notifications
    Runs every 5 minutes
    """
    try:
        from models.notification_dlq import NotificationDLQ

        unresolved_count = NotificationDLQ.query.filter_by(resolved=False).count()

        if unresolved_count > 0:
            logger.warning(f"{unresolved_count} notifications in DLQ need attention")

        return {'unresolved_count': unresolved_count}

    except Exception as e:
        logger.error(f"Error processing DLQ: {str(e)}")
        return {'error': str(e)}


@celery_app.task(name='workers.tasks.bulk_send_notifications')
def bulk_send_notifications(notification_ids: list):
    """
    Send multiple notifications in bulk

    Args:
        notification_ids: List of notification IDs to send
    """
    results = []
    for notification_id in notification_ids:
        result = send_notification.delay(notification_id)
        results.append(result.id)

    return {'task_ids': results, 'count': len(results)}
