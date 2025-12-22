package main

import (
	"log"
	"os"
	"os/signal"
	"syscall"

	"notification_system/configs"
	"notification_system/workers"
)

func main() {
	db := configs.ConnectDatabase()
	if db == nil {
		log.Fatal("Cannot connect to database")
	}

	redisClient := configs.ConnectRedisClient()
	if redisClient == nil {
		log.Fatal("Cannot connect to Redis")
	}

	workerCount := 4
	if envCount := os.Getenv("WORKER_COUNT"); envCount != "" {
		log.Printf("Using %s workers from environment\n", envCount)
	}

	worker := workers.NewWorker(db, redisClient, workerCount)
	worker.Start()

	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)

	log.Println("Worker is running. Press Ctrl+C to stop.")

	<-sigChan

	log.Println("\nReceived shutdown signal")
	worker.Stop()

	log.Println("Worker shutdown complete")
}
