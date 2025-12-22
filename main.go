package main

import (
	"log"
	"notification_system/configs"
	"notification_system/core"
	"notification_system/handlers"
	"notification_system/models"
)

func main() {
	db := configs.ConnectDatabase()
	redisClient := configs.ConnectRedisClient()
	if redisClient == nil {
		log.Fatal("Cannot connect to redis database")
	}
	if db == nil {
		log.Fatal("Cannot connect the database")
	}
	if err := db.AutoMigrate(
		&models.Users{},
		&models.Notification{},
		&models.NotificationDLQ{},
		&models.NotificationPreference{},
		&models.NotificationTemplate{},
		&models.NotificationWebhook{},
		&models.WebhookDelivery{},
		&models.APIKey{},
		&models.ProviderConfig{},
		&models.NotificationMetric{},
		&models.RateLimit{},
		&models.AuditLog{},
	); err != nil {
		log.Fatalf("auto migrate failed: %v", err)
	}

	notificationService := &core.NotificationService{
		DB:  db,
		RDB: redisClient,
	}
	notificationHandler := &handlers.NotificationHandler{
		Service: notificationService,
	}
	userHandler := &handlers.UserHandler{}

	router := configs.SetupRouter()
	api := router.Group("/api/v1")
	{
		api.POST("/users", userHandler.CreateUser)
		notificationHandler.RegisterRoutes(api)
	}
	if err := router.Run(":8080"); err != nil {
		log.Fatal(err)
	}
}
