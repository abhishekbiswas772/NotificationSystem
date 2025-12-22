from configs.db import db
from configs.redis import get_redis_pool
from helpers.custom_exceptions import RetryHandlerException
from helpers.constants import Constants
from helpers.helpers import now_ms
from models.notification import Notification
from helpers.enums import NotificationStatus
from handlers.dlq_handler import DLQHandler
from datetime import datetime, timedelta, timezone
import random
import json

class RetryHandler:
    def __init__(self):
        self.db = db
        self.redis_client = get_redis_pool()
        if not self.db:
            raise RetryHandlerException("cannot connect to database")
        
        if not self.redis_client:
            raise RetryHandlerException("cannot redis client")
    
    def clean_old_retry(self):
        try:
            cutoff = int((datetime.now(timezone.utc) - timedelta(days=7)).timestamp())
            self.redis_client.zremrangebyscore(
                "notification:retries",
                min="-inf",
                max=cutoff,
            )
        except Exception as e:
            print(e)
            raise RetryHandlerException(str(e))
        
    def process_due_retries(self) -> int:
        try:
            current_time = int(now_ms())
            try:
                notifications = (
                    Notification.query.filter(
                        Notification.status == NotificationStatus.PENDING,
                        Notification.send_at.isnot(None),
                        Notification.send_at <= current_time,
                    ).limit(100)
                    .all()
                )
            except Exception as e:
                raise RetryHandlerException(f"failed to fetch due notifications: {e}")
            if not notifications:
                return 0
            processed = 0
            for notification in notifications:
                notification_data = json.dumps({
                    "id" : notification.id,
                    "action" : "send"
                })
                
                try:
                    self.redis_client.lpush("notification:queue", notification_data)
                    processed += 1
                except Exception as e:
                    print(e)
                    continue
            return processed
        except Exception as e:
            print(e)
            raise RetryHandlerException(str(e))

    def calculate_delay(self, attempts : int) -> int:
        base_delay = float(Constants.BASE_DELAY)
        exp_delay = float(Constants.EXPONENTIAL_BASE)
        max_delay = float(Constants.MAX_DELAY)

        delay = base_delay * (exp_delay ** float(attempts))
        if delay > max_delay:
            delay = max_delay
        jitter = random.random() * delay * 0.1
        return int(delay + jitter)
    
    def schedule_retry(self, notification_id: str, attempts : int, error_message: str):
        if not notification_id or notification_id == "":
            raise RetryHandlerException("notification id is missing")
        try:
            notification = Notification.query.filter_by(id=notification_id).first()
            if not notification:
                raise RetryHandlerException("Notification not found with this id")

            if attempts >= notification.max_retries:
                dlq_handler = DLQHandler()
                dlq_handler.move_to_dlq(
                    notification_id=notification_id,
                    reason="max_retries_exceeded",
                    error_details=error_message or "max retry attempts exceeded",
                )
                return {"status": "moved_to_dlq", "notification_id": notification_id}

            delay = self.calculate_delay(attempts=attempts)
            next_retry_time = datetime.now(timezone.utc).timestamp() + delay
            notification.attempt_count = attempts
            notification.last_attempted = now_ms()
            notification.send_at = int(next_retry_time * 1000)
            notification.status = NotificationStatus.PENDING
            notification.error_message = error_message
            self.db.session.commit()
            retry_info = {
                "notification_id": notification_id,
                "attempt": attempts,
                "retry_at": int(next_retry_time),
            }
            self.redis_client.zadd("notification:retries", {json.dumps(retry_info): next_retry_time})
            return retry_info
        except Exception as e:
            print(e)
            raise RetryHandlerException(str(e))
