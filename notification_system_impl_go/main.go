package main

import (
	"log"
	"strings"

	"notification_system/configs"
	"notification_system/core"
	"notification_system/handlers"
	"notification_system/models"

	"fmt"

	"gorm.io/gorm"
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

	// Drop and recreate schema to fix column name mismatches
	if err := resetDatabaseSchema(db); err != nil {
		log.Printf("Warning: Could not reset schema: %v", err)
	}

	modelsToMigrate := []interface{}{
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
	}

	for _, m := range modelsToMigrate {
		if err := db.AutoMigrate(m); err != nil {
			if strings.Contains(err.Error(), `constraint "uni_users_email"`) {
				log.Printf("Skipping missing constraint during migration: %v", err)
				continue
			}
			log.Fatalf("auto migrate failed for %T: %v", m, err)
		}
	}

	if err := ensureNotificationColumns(db); err != nil {
		log.Fatalf("failed to ensure notification columns: %v", err)
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

func resetDatabaseSchema(db *gorm.DB) error {
	log.Println("Resetting database schema...")

	// Drop all tables in reverse order (respecting foreign keys)
	tables := []string{
		"audit_logs",
		"rate_limits",
		"notification_metrics",
		"provider_configs",
		"api_keys",
		"webhook_deliveries",
		"notification_webhooks",
		"notification_templates",
		"notification_preferences",
		"notification_dlq",
		"notifications",
		"users",
	}

	for _, table := range tables {
		if err := db.Exec(fmt.Sprintf("DROP TABLE IF EXISTS %s CASCADE", table)).Error; err != nil {
			log.Printf("Warning dropping table %s: %v", table, err)
		}
	}

	// Drop existing enum types
	enumTypes := []string{
		"DROP TYPE IF EXISTS messagetype CASCADE",
		"DROP TYPE IF EXISTS providertype CASCADE",
		"DROP TYPE IF EXISTS notificationstatus CASCADE",
	}

	for _, stmt := range enumTypes {
		if err := db.Exec(stmt).Error; err != nil {
			log.Printf("Warning dropping enum type: %v", err)
		}
	}

	log.Println("Schema reset complete. Tables will be recreated by AutoMigrate.")
	return nil
}

func ensureNotificationColumns(db *gorm.DB) error {
	type columnSpec struct {
		model interface{}
		name  string
	}

	required := []columnSpec{
		{model: &models.Notification{}, name: "CreatedAt"},
		{model: &models.Notification{}, name: "UpdatedAt"},
		{model: &models.Notification{}, name: "SendAt"},
		{model: &models.Notification{}, name: "FailedAt"},
		{model: &models.Notification{}, name: "SentAt"},
		{model: &models.Notification{}, name: "ErrorMessage"},
		{model: &models.Notification{}, name: "ProviderResponse"},
	}

	migrator := db.Migrator()
	for _, col := range required {
		if !migrator.HasColumn(col.model, col.name) {
			if err := migrator.AddColumn(col.model, col.name); err != nil {
				return fmt.Errorf("add column %s: %w", col.name, err)
			}
		}
	}
	return nil
}
