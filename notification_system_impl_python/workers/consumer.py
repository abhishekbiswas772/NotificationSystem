#!/usr/bin/env python3
"""
Redis Queue Consumer
Continuously consumes from notification:queue and dispatches to Celery workers
"""

import time
import logging
from configs.redis import get_redis_pool
from workers.tasks import send_notification
import json
import signal
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

running = True


def signal_handler(sig, frame):
    """Handle shutdown signals"""
    global running
    logger.info("Received shutdown signal, stopping consumer...")
    running = False


def consume_queue():
    """Main consumer loop"""
    global running

    redis_client = get_redis_pool()
    logger.info("Starting notification queue consumer...")

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    processed_count = 0

    while running:
        try:
            item = redis_client.brpop('notification:queue', timeout=1)

            if item:
                _, payload = item
                data = json.loads(payload)
                notification_id = data.get('id')
                action = data.get('action', 'send')

                if notification_id and action == 'send':
                    send_notification.delay(notification_id)
                    processed_count += 1

                    if processed_count % 10 == 0:
                        logger.info(f"Dispatched {processed_count} notifications")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in queue: {e}")

        except Exception as e:
            logger.error(f"Error consuming queue: {e}")
            time.sleep(1)

    logger.info(f"Consumer stopped. Total processed: {processed_count}")


if __name__ == '__main__':
    consume_queue()
