#!/bin/bash

echo "Starting Notification System Workers (Go)..."

export WORKER_COUNT=${WORKER_COUNT:-4}

echo "Starting worker with $WORKER_COUNT concurrent consumers..."

go build -o bin/worker ./cmd/worker

if [ $? -eq 0 ]; then
    echo "Worker built successfully"
    echo "Starting worker process..."
    ./bin/worker
else
    echo "Failed to build worker"
    exit 1
fi
