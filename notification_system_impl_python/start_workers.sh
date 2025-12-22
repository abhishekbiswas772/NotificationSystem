#!/bin/bash

echo "Starting Notification System Workers..."

echo "Starting Celery worker..."
celery -A celery_app worker --loglevel=info --concurrency=4 &
CELERY_WORKER_PID=$!

echo "Starting Celery Beat scheduler..."
celery -A celery_app beat --loglevel=info &
CELERY_BEAT_PID=$!

echo "Starting Redis Queue Consumer..."
python workers/consumer.py &
CONSUMER_PID=$!

echo ""
echo "All workers started!"
echo "  - Celery Worker PID: $CELERY_WORKER_PID"
echo "  - Celery Beat PID: $CELERY_BEAT_PID"
echo "  - Queue Consumer PID: $CONSUMER_PID"
echo ""
echo "Press Ctrl+C to stop all workers"

trap "kill $CELERY_WORKER_PID $CELERY_BEAT_PID $CONSUMER_PID; exit" INT TERM

wait
