# Notification System - Implementation Guide

## What's Been Completed ✅

### 1. Models (All Complete)
- ✅ `models/users.go` - User model with relationships
- ✅ `models/notifications.go` - Notification and NotificationDLQ models with status enums
- ✅ `models/notification_preferences.go` - User notification preferences
- ✅ `models/notification_templates.go` - Reusable templates
- ✅ `models/notification_webhooks.go` - Webhook configurations
- ✅ `models/webhook_deliveries.go` - Webhook delivery tracking
- ✅ `models/api_keys.go` - API key authentication
- ✅ `models/rate_limits.go` - Rate limiting
- ✅ `models/audit_logs.go` - Audit trail
- ✅ `models/notification_metrics.go` - Analytics
- ✅ `models/provider_configs.go` - Provider configurations

### 2. Core Business Logic (Complete)
- ✅ `core/notification_service.go` - CRUD operations for notifications
- ✅ `core/retrys.go` - Complete retry logic with exponential backoff
- ✅ `core/dlqHandler.go` - Complete DLQ management
- ✅ `core/provider.go` - Provider interface and mock implementation

### 3. Configuration (Complete)
- ✅ `configs/configs.go` - PostgreSQL configuration
- ✅ `configs/redisConfigs.go` - Redis configuration
- ✅ `configs/ginConfigs.go` - Basic Gin setup

### 4. Handlers (Partial)
- ✅ `handlers/userHandlers.go` - User creation
- ✅ `handlers/notificationHandlers.go` - Notification CRUD endpoints

---

## What Needs to Be Implemented 🚧

### 1. Worker Pool (`core/worker.go`)

Create a worker pool that processes notifications from the Redis queue:

```go
package core

import (
	"context"
	"encoding/json"
	"log"
	"sync"
	"time"

	"github.com/redis/go-redis/v9"
	"gorm.io/gorm"

	"notification_system/models"
)

type Worker struct {
	ID       int
	DB       *gorm.DB
	RDB      *redis.Client
	Provider NotificationProvider
	Retry    *RetryManager
}

type WorkerPool struct {
	Workers    []*Worker
	DB         *gorm.DB
	RDB        *redis.Client
	Providers  map[models.ProviderType]NotificationProvider
	NumWorkers int
	wg         sync.WaitGroup
	stopChan   chan struct{}
}

func NewWorkerPool(db *gorm.DB, rdb *redis.Client, numWorkers int) *WorkerPool {
	// Initialize providers
	providers := map[models.ProviderType]NotificationProvider{
		models.SENDGRID: &MockProvider{}, // Replace with real SendGridProvider
		models.TWILIO:   &MockProvider{}, // Replace with real TwilioProvider
		models.FCM:      &MockProvider{}, // Replace with real FCMProvider
	}

	pool := &WorkerPool{
		DB:         db,
		RDB:        rdb,
		Providers:  providers,
		NumWorkers: numWorkers,
		Workers:    make([]*Worker, numWorkers),
		stopChan:   make(chan struct{}),
	}

	// Create workers
	for i := 0; i < numWorkers; i++ {
		pool.Workers[i] = &Worker{
			ID:       i,
			DB:       db,
			RDB:      rdb,
			Provider: &MockProvider{},
			Retry:    &RetryManager{DB: db, RDB: rdb},
		}
	}

	return pool
}

func (wp *WorkerPool) Start(ctx context.Context) {
	log.Printf("Starting worker pool with %d workers", wp.NumWorkers)

	for _, worker := range wp.Workers {
		wp.wg.Add(1)
		go worker.Run(ctx, &wp.wg, wp.stopChan, wp.Providers)
	}
}

func (wp *WorkerPool) Stop() {
	log.Println("Stopping worker pool...")
	close(wp.stopChan)
	wp.wg.Wait()
	log.Println("Worker pool stopped")
}

func (w *Worker) Run(ctx context.Context, wg *sync.WaitGroup, stopChan chan struct{}, providers map[models.ProviderType]NotificationProvider) {
	defer wg.Done()
	log.Printf("Worker %d started", w.ID)

	for {
		select {
		case <-stopChan:
			log.Printf("Worker %d stopping", w.ID)
			return
		default:
			w.processNext(ctx, providers)
		}
	}
}

func (w *Worker) processNext(ctx context.Context, providers map[models.ProviderType]NotificationProvider) {
	// Pop from Redis queue (blocking with 1 second timeout)
	result, err := w.RDB.BRPop(ctx, 1*time.Second, "notification:queue").Result()
	if err != nil {
		if err != redis.Nil {
			log.Printf("Worker %d: Error popping from queue: %v", w.ID, err)
		}
		return
	}

	if len(result) < 2 {
		return
	}

	var task map[string]string
	if err := json.Unmarshal([]byte(result[1]), &task); err != nil {
		log.Printf("Worker %d: Error unmarshaling task: %v", w.ID, err)
		return
	}

	notificationID := task["id"]
	log.Printf("Worker %d: Processing notification %s", w.ID, notificationID)

	// Get notification from database
	var notification models.Notification
	if err := w.DB.WithContext(ctx).First(&notification, "id = ?", notificationID).Error; err != nil {
		log.Printf("Worker %d: Error fetching notification: %v", w.ID, err)
		return
	}

	// Get the appropriate provider
	provider, ok := providers[notification.Provider]
	if !ok {
		log.Printf("Worker %d: Unknown provider %s", w.ID, notification.Provider)
		return
	}

	// Send notification
	err = provider.Send(ctx, &notification)

	// Update attempt count
	notification.AttemptCount++
	now := time.Now().UnixMilli()
	notification.LastAttempted = &now

	if err != nil {
		log.Printf("Worker %d: Failed to send notification %s: %v", w.ID, notificationID, err)
		errorMsg := err.Error()
		notification.ErrorMessage = &errorMsg

		// Schedule retry
		if notification.AttemptCount < notification.MaxRetries {
			if err := w.Retry.ScheduleRetry(ctx, notificationID, notification.AttemptCount, errorMsg); err != nil {
				log.Printf("Worker %d: Error scheduling retry: %v", w.ID, err)
			}
		} else {
			log.Printf("Worker %d: Max retries reached for %s", w.ID, notificationID)
		}
	} else {
		log.Printf("Worker %d: Successfully sent notification %s", w.ID, notificationID)
	}

	// Save notification
	if err := w.DB.WithContext(ctx).Save(&notification).Error; err != nil {
		log.Printf("Worker %d: Error saving notification: %v", w.ID, err)
	}
}
```

---

### 2. Scheduler (`core/scheduler.go`)

Create a cron-based scheduler for periodic tasks:

```go
package core

import (
	"context"
	"log"

	"github.com/redis/go-redis/v9"
	"github.com/robfig/cron/v3"
	"gorm.io/gorm"
)

type Scheduler struct {
	cron       *cron.Cron
	DB         *gorm.DB
	RDB        *redis.Client
	retryMgr   *RetryManager
	dlqMgr     *DLQManager
}

func NewScheduler(db *gorm.DB, rdb *redis.Client) *Scheduler {
	return &Scheduler{
		cron:     cron.New(),
		DB:       db,
		RDB:      rdb,
		retryMgr: &RetryManager{DB: db, RDB: rdb},
		dlqMgr:   &DLQManager{DB: db},
	}
}

func (s *Scheduler) Start() error {
	log.Println("Starting scheduler...")

	// Process due retries every minute
	s.cron.AddFunc("@every 1m", func() {
		ctx := context.Background()
		count, err := s.retryMgr.ProcessDueRetries(ctx)
		if err != nil {
			log.Printf("Error processing retries: %v", err)
		} else if count > 0 {
			log.Printf("Processed %d due notifications", count)
		}
	})

	// Cleanup old retries every hour
	s.cron.AddFunc("@every 1h", func() {
		ctx := context.Background()
		if err := s.retryMgr.CleanupOldRetries(ctx); err != nil {
			log.Printf("Error cleaning up old retries: %v", err)
		}
	})

	// Cleanup old DLQ entries daily
	s.cron.AddFunc("@daily", func() {
		ctx := context.Background()
		count, err := s.dlqMgr.CleanupOldDLQEntries(ctx, 30) // 30 days
		if err != nil {
			log.Printf("Error cleaning up DLQ: %v", err)
		} else {
			log.Printf("Cleaned up %d old DLQ entries", count)
		}
	})

	// DLQ stats logging every hour
	s.cron.AddFunc("@every 1h", func() {
		ctx := context.Background()
		stats, err := s.dlqMgr.GetDLQStats(ctx)
		if err != nil {
			log.Printf("Error getting DLQ stats: %v", err)
		} else {
			log.Printf("DLQ Stats: %+v", stats)
		}
	})

	s.cron.Start()
	log.Println("Scheduler started")
	return nil
}

func (s *Scheduler) Stop() {
	log.Println("Stopping scheduler...")
	s.cron.Stop()
	log.Println("Scheduler stopped")
}
```

**Install the cron package:**
```bash
go get github.com/robfig/cron/v3
```

---

### 3. Real Provider Implementations

#### SendGrid Provider (`core/providers/sendgrid.go`)

```go
package providers

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/sendgrid/sendgrid-go"
	"github.com/sendgrid/sendgrid-go/helpers/mail"

	"notification_system/models"
)

type SendGridProvider struct {
	APIKey string
	Client *sendgrid.Client
}

func NewSendGridProvider(apiKey string) *SendGridProvider {
	return &SendGridProvider{
		APIKey: apiKey,
		Client: sendgrid.NewSendClient(apiKey),
	}
}

func (s *SendGridProvider) ProviderName() string {
	return "sendgrid"
}

func (s *SendGridProvider) Send(ctx context.Context, notification *models.Notification) error {
	// Parse payload
	var payload map[string]interface{}
	if err := json.Unmarshal([]byte(notification.Payload), &payload); err != nil {
		return fmt.Errorf("invalid payload: %w", err)
	}

	from := mail.NewEmail("", payload["from"].(string))
	to := mail.NewEmail("", payload["to"].(string))
	subject := payload["subject"].(string)
	plainTextContent := payload["body"].(string)
	htmlContent := payload["body"].(string)

	message := mail.NewSingleEmail(from, subject, to, plainTextContent, htmlContent)

	response, err := s.Client.SendWithContext(ctx, message)
	if err != nil {
		return fmt.Errorf("sendgrid send failed: %w", err)
	}

	if response.StatusCode >= 400 {
		return fmt.Errorf("sendgrid returned error status %d: %s", response.StatusCode, response.Body)
	}

	// Update notification
	notification.Status = models.StatusSent
	now := time.Now().UnixMilli()
	notification.SentAt = &now
	responseBody := response.Body
	notification.ProviderResponse = &responseBody

	return nil
}
```

**Install SendGrid:**
```bash
go get github.com/sendgrid/sendgrid-go
```

---

#### Twilio Provider (`core/providers/twilio.go`)

```go
package providers

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/twilio/twilio-go"
	twilioApi "github.com/twilio/twilio-go/rest/api/v2010"

	"notification_system/models"
)

type TwilioProvider struct {
	AccountSID string
	AuthToken  string
	FromNumber string
	Client     *twilio.RestClient
}

func NewTwilioProvider(accountSID, authToken, fromNumber string) *TwilioProvider {
	client := twilio.NewRestClientWithParams(twilio.ClientParams{
		Username: accountSID,
		Password: authToken,
	})

	return &TwilioProvider{
		AccountSID: accountSID,
		AuthToken:  authToken,
		FromNumber: fromNumber,
		Client:     client,
	}
}

func (t *TwilioProvider) ProviderName() string {
	return "twilio"
}

func (t *TwilioProvider) Send(ctx context.Context, notification *models.Notification) error {
	// Parse payload
	var payload map[string]interface{}
	if err := json.Unmarshal([]byte(notification.Payload), &payload); err != nil {
		return fmt.Errorf("invalid payload: %w", err)
	}

	params := &twilioApi.CreateMessageParams{}
	params.SetTo(payload["to"].(string))
	params.SetFrom(t.FromNumber)
	params.SetBody(payload["body"].(string))

	resp, err := t.Client.Api.CreateMessage(params)
	if err != nil {
		return fmt.Errorf("twilio send failed: %w", err)
	}

	// Update notification
	notification.Status = models.StatusSent
	now := time.Now().UnixMilli()
	notification.SentAt = &now
	responseStr := fmt.Sprintf("MessageSID: %s, Status: %s", *resp.Sid, *resp.Status)
	notification.ProviderResponse = &responseStr

	return nil
}
```

**Install Twilio:**
```bash
go get github.com/twilio/twilio-go
```

---

### 4. Complete Main.go

Update your `main.go` to wire everything together:

```go
package main

import (
	"context"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gin-gonic/gin"

	"notification_system/configs"
	"notification_system/core"
	"notification_system/core/providers"
	"notification_system/handlers"
	"notification_system/models"
)

func main() {
	log.Println("Starting Notification System...")

	// Initialize database
	db := configs.ConnectDatabase()
	if db == nil {
		log.Fatal("Failed to connect to database")
	}

	// Initialize Redis
	redis := configs.ConnectRedisClient()
	if redis == nil {
		log.Fatal("Failed to connect to Redis")
	}

	// Run migrations
	log.Println("Running database migrations...")
	if err := db.AutoMigrate(
		&models.Users{},
		&models.Notification{},
		&models.NotificationDLQ{},
		&models.NotificationPreference{},
		&models.NotificationTemplate{},
		&models.NotificationWebhook{},
		&models.WebhookDelivery{},
		&models.APIKey{},
		&models.RateLimit{},
		&models.AuditLog{},
		&models.NotificationMetric{},
		&models.ProviderConfig{},
	); err != nil {
		log.Fatalf("Migration failed: %v", err)
	}

	// Setup providers (replace with real API keys from env)
	sendgridAPIKey := os.Getenv("SENDGRID_API_KEY")
	twilioAccountSID := os.Getenv("TWILIO_ACCOUNT_SID")
	twilioAuthToken := os.Getenv("TWILIO_AUTH_TOKEN")
	twilioFromNumber := os.Getenv("TWILIO_FROM_NUMBER")

	providerMap := make(map[models.ProviderType]core.NotificationProvider)

	if sendgridAPIKey != "" {
		providerMap[models.SENDGRID] = providers.NewSendGridProvider(sendgridAPIKey)
	} else {
		providerMap[models.SENDGRID] = &core.MockProvider{}
	}

	if twilioAccountSID != "" && twilioAuthToken != "" {
		providerMap[models.TWILIO] = providers.NewTwilioProvider(twilioAccountSID, twilioAuthToken, twilioFromNumber)
	} else {
		providerMap[models.TWILIO] = &core.MockProvider{}
	}

	providerMap[models.FCM] = &core.MockProvider{} // Add real FCM provider

	// Start worker pool
	workerPool := core.NewWorkerPool(db, redis, 5) // 5 workers
	ctx := context.Background()
	workerPool.Start(ctx)

	// Start scheduler
	scheduler := core.NewScheduler(db, redis)
	if err := scheduler.Start(); err != nil {
		log.Fatalf("Failed to start scheduler: %v", err)
	}

	// Setup HTTP server
	router := gin.Default()

	// Health check
	router.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{"status": "ok"})
	})

	// API routes
	v1 := router.Group("/api/v1")
	{
		// User routes
		userHandler := &handlers.UserHandler{}
		v1.POST("/users", userHandler.CreateUser)

		// Notification routes
		notifService := &core.NotificationService{DB: db, RDB: redis}
		notifHandler := &handlers.NotificationHandler{Service: notifService}
		notifHandler.RegisterRoutes(v1)
	}

	// Graceful shutdown
	go func() {
		if err := router.Run(":8080"); err != nil {
			log.Fatalf("Server failed: %v", err)
		}
	}()

	log.Println("Server started on :8080")

	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("Shutting down gracefully...")

	// Stop workers and scheduler
	workerPool.Stop()
	scheduler.Stop()

	// Give processes time to finish
	time.Sleep(2 * time.Second)

	log.Println("Server exited")
}
```

---

### 5. Environment Configuration

Create `.env.example`:

```env
# Database
DATABASE_URL=postgres://user:password@localhost:5432/notification_system?sslmode=disable

# Redis
REDIS_ADDR=localhost:6379
REDIS_PASSWORD=

# SendGrid
SENDGRID_API_KEY=your-sendgrid-api-key

# Twilio
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_FROM_NUMBER=+1234567890

# FCM
FCM_SERVER_KEY=your-fcm-server-key

# Server
PORT=8080
GIN_MODE=release
```

---

## Running the System

1. **Install dependencies:**
```bash
go mod tidy
```

2. **Setup PostgreSQL and Redis:**
```bash
# Using Docker
docker run --name postgres -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres
docker run --name redis -p 6379:6379 -d redis
```

3. **Create `.env` file:**
```bash
cp .env.example .env
# Edit .env with your actual credentials
```

4. **Run migrations:**
```bash
go run main.go
```

5. **Test the API:**
```bash
# Create a user
curl -X POST http://localhost:8080/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "username": "testuser"}'

# Create a notification
curl -X POST http://localhost:8080/api/v1/notifications \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "<user-id-from-above>",
    "message_type": "email",
    "provider": "sendgrid",
    "payload": "{\"to\":\"recipient@example.com\",\"from\":\"sender@example.com\",\"subject\":\"Test\",\"body\":\"Hello World\"}"
  }'
```

---

## Next Steps

1. Add authentication middleware
2. Add rate limiting middleware
3. Implement remaining handlers (templates, webhooks, preferences)
4. Add comprehensive tests
5. Add metrics and monitoring
6. Deploy to production

---

## Architecture Overview

```
Client Request
     ↓
API Layer (Gin)
     ↓
Service Layer (NotificationService)
     ↓
Redis Queue
     ↓
Worker Pool (5 workers)
     ↓
Providers (SendGrid/Twilio/FCM)
     ↓
External Services
     ↓
Update DB & Redis
     ↓
(If failed) → Retry Manager → DLQ
     ↓
Scheduler (Cron) → Process Retries
```

---

Good luck with your notification system! 🚀
