package workers

import (
	"context"
	"encoding/json"
	"log"
	"sync"
	"time"

	"github.com/redis/go-redis/v9"
	"gorm.io/gorm"

	"notification_system/core"
	"notification_system/core/providers"
	"notification_system/models"
)

type Worker struct {
	DB              *gorm.DB
	RDB             *redis.Client
	ProviderMap     map[models.ProviderType]providers.NotificationProvider
	Ctx             context.Context
	Cancel          context.CancelFunc
	WorkerCount     int
	wg              sync.WaitGroup
	retryManager    *core.RetryManager
	dlqManager      *core.DLQManager
}

type QueueMessage struct {
	ID     string `json:"id"`
	Action string `json:"action"`
}

func NewWorker(db *gorm.DB, rdb *redis.Client, workerCount int) *Worker {
	ctx, cancel := context.WithCancel(context.Background())

	return &Worker{
		DB:           db,
		RDB:          rdb,
		ProviderMap:  providers.GetProviderMap(),
		Ctx:          ctx,
		Cancel:       cancel,
		WorkerCount:  workerCount,
		retryManager: &core.RetryManager{DB: db, RDB: rdb},
		dlqManager:   &core.DLQManager{DB: db},
	}
}

func (w *Worker) Start() {
	log.Println("🚀 Starting notification workers...")

	for i := 0; i < w.WorkerCount; i++ {
		w.wg.Add(1)
		go w.consumeQueue(i + 1)
	}

	w.wg.Add(1)
	go w.runRetryProcessor()

	w.wg.Add(1)
	go w.runDLQMonitor()

	w.wg.Add(1)
	go w.runCleanupJob()

	log.Printf("✓ Started %d queue consumers + 3 background jobs\n", w.WorkerCount)
}

func (w *Worker) Stop() {
	log.Println("⏹ Stopping workers...")
	w.Cancel()
	w.wg.Wait()
	log.Println("✓ All workers stopped")
}

func (w *Worker) consumeQueue(workerID int) {
	defer w.wg.Done()

	log.Printf("Worker #%d started\n", workerID)

	for {
		select {
		case <-w.Ctx.Done():
			log.Printf("Worker #%d shutting down\n", workerID)
			return
		default:
			result, err := w.RDB.BRPop(w.Ctx, 1*time.Second, "notification:queue").Result()
			if err == redis.Nil {
				continue
			}
			if err != nil {
				log.Printf("Worker #%d error: %v\n", workerID, err)
				continue
			}

			if len(result) < 2 {
				continue
			}

			var msg QueueMessage
			if err := json.Unmarshal([]byte(result[1]), &msg); err != nil {
				log.Printf("Worker #%d: Invalid JSON: %v\n", workerID, err)
				continue
			}

			if msg.ID != "" && msg.Action == "send" {
				w.processNotification(workerID, msg.ID)
			}
		}
	}
}

func (w *Worker) processNotification(workerID int, notificationID string) {
	ctx, cancel := context.WithTimeout(w.Ctx, 30*time.Second)
	defer cancel()

	var notification models.Notification
	if err := w.DB.WithContext(ctx).First(&notification, "id = ?", notificationID).Error; err != nil {
		log.Printf("Worker #%d: Notification %s not found: %v\n", workerID, notificationID, err)
		return
	}

	if notification.Status == models.StatusSent || notification.Status == models.StatusCancelled {
		log.Printf("Worker #%d: Notification %s already %s\n", workerID, notificationID, notification.Status)
		return
	}

	notification.AttemptCount++
	now := time.Now().UnixMilli()
	notification.LastAttempted = &now

	if err := w.DB.WithContext(ctx).Save(&notification).Error; err != nil {
		log.Printf("Worker #%d: Failed to update notification %s: %v\n", workerID, notificationID, err)
		return
	}

	provider := w.ProviderMap[notification.Provider]
	if provider == nil {
		errMsg := "provider not configured"
		notification.ErrorMessage = &errMsg
		w.DB.WithContext(ctx).Save(&notification)
		w.retryManager.ScheduleRetry(ctx, notificationID, notification.AttemptCount, errMsg)
		return
	}

	log.Printf("Worker #%d: Sending notification %s via %s\n", workerID, notificationID, provider.ProviderName())

	if err := provider.Send(ctx, &notification); err != nil {
		errMsg := err.Error()
		notification.Status = models.StatusFailed
		notification.ErrorMessage = &errMsg
		w.DB.WithContext(ctx).Save(&notification)

		log.Printf("Worker #%d: ✗ Notification %s failed: %v\n", workerID, notificationID, err)
		w.retryManager.ScheduleRetry(ctx, notificationID, notification.AttemptCount, errMsg)
	} else {
		notification.Status = models.StatusSent
		w.DB.WithContext(ctx).Save(&notification)
		log.Printf("Worker #%d: ✓ Notification %s sent successfully\n", workerID, notificationID)
	}
}

func (w *Worker) runRetryProcessor() {
	defer w.wg.Done()

	ticker := time.NewTicker(60 * time.Second)
	defer ticker.Stop()

	log.Println("Retry processor started (runs every 60s)")

	for {
		select {
		case <-w.Ctx.Done():
			log.Println("Retry processor shutting down")
			return
		case <-ticker.C:
			count, err := w.retryManager.ProcessDueRetries(w.Ctx)
			if err != nil {
				log.Printf("Retry processor error: %v\n", err)
			} else if count > 0 {
				log.Printf("Retry processor: Queued %d notifications for retry\n", count)
			}
		}
	}
}

func (w *Worker) runDLQMonitor() {
	defer w.wg.Done()

	ticker := time.NewTicker(5 * time.Minute)
	defer ticker.Stop()

	log.Println("DLQ monitor started (runs every 5 minutes)")

	for {
		select {
		case <-w.Ctx.Done():
			log.Println("DLQ monitor shutting down")
			return
		case <-ticker.C:
			var count int64
			if err := w.DB.Model(&models.NotificationDLQ{}).Where("resolved = ?", false).Count(&count).Error; err != nil {
				log.Printf("DLQ monitor error: %v\n", err)
			} else if count > 0 {
				log.Printf("⚠ DLQ monitor: %d unresolved notifications in DLQ\n", count)
			}
		}
	}
}

func (w *Worker) runCleanupJob() {
	defer w.wg.Done()

	ticker := time.NewTicker(24 * time.Hour)
	defer ticker.Stop()

	log.Println("Cleanup job started (runs daily)")

	for {
		select {
		case <-w.Ctx.Done():
			log.Println("Cleanup job shutting down")
			return
		case <-ticker.C:
			if err := w.retryManager.CleanupOldRetries(w.Ctx); err != nil {
				log.Printf("Cleanup job error: %v\n", err)
			} else {
				log.Println("Cleanup job: Old retry records cleaned up")
			}
		}
	}
}
