package core

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"math"
	"math/rand"
	"time"

	"github.com/redis/go-redis/v9"
	"gorm.io/gorm"

	"notification_system/models"
)

const (
	MAX_ATTEMPTS     int = 5
	BASE_DELAY       int = 60  // 1 minute
	MAX_DELAY        int = 3600 // 1 hour
	EXPONENTIAL_BASE int = 2
)

type RetryManager struct {
	DB  *gorm.DB
	RDB *redis.Client
}

// calculateDelay calculates exponential backoff delay with jitter
func calculateDelay(attempt int) int {
	baseDelay := float64(BASE_DELAY)
	expBase := float64(EXPONENTIAL_BASE)
	maxDelay := float64(MAX_DELAY)

	delay := baseDelay * math.Pow(expBase, float64(attempt))
	if delay > maxDelay {
		delay = maxDelay
	}
	// Add jitter (±10% of delay)
	jitter := rand.Float64() * delay * 0.1
	return int(delay + jitter)
}

// scheduleRetry calculates the next retry time
func scheduleRetry(attempt int) time.Time {
	if attempt >= MAX_ATTEMPTS {
		return time.Time{}
	}
	seconds := calculateDelay(attempt)
	return time.Now().Add(time.Duration(seconds) * time.Second)
}

// ScheduleRetry schedules a retry for a failed notification
func (rm *RetryManager) ScheduleRetry(ctx context.Context, notificationID string, attempt int, errorMsg string) error {
	if rm.DB == nil {
		return fmt.Errorf("database not initialized")
	}

	var notification models.Notification
	if err := rm.DB.WithContext(ctx).First(&notification, "id = ?", notificationID).Error; err != nil {
		return fmt.Errorf("notification not found: %w", err)
	}

	// Check if max attempts exceeded
	if attempt >= notification.MaxRetries {
		log.Printf("Max retry attempts (%d) exceeded for notification %s, moving to DLQ", notification.MaxRetries, notificationID)
		// Move to DLQ
		dlqManager := &DLQManager{DB: rm.DB}
		return dlqManager.MoveToDLQ(ctx, notificationID, "max_retries_exceeded", errorMsg)
	}

	// Calculate retry delay
	delay := calculateDelay(attempt)
	nextRetryTime := time.Now().Add(time.Duration(delay) * time.Second)

	// Update notification with retry info
	now := time.Now().UnixMilli()
	updates := map[string]interface{}{
		"attempt_count":  attempt,
		"last_attempted": now,
		"send_at":        nextRetryTime.UnixMilli(),
		"status":         models.StatusPending,
		"error_message":  errorMsg,
	}

	if err := rm.DB.WithContext(ctx).Model(&notification).Updates(updates).Error; err != nil {
		return fmt.Errorf("failed to update notification for retry: %w", err)
	}

	// Queue the retry in Redis for the scheduler to pick up
	if rm.RDB != nil {
		retryInfo := map[string]interface{}{
			"notification_id": notificationID,
			"attempt":         attempt,
			"retry_at":        nextRetryTime.Unix(),
		}
		data, _ := json.Marshal(retryInfo)
		if err := rm.RDB.ZAdd(ctx, "notification:retries", redis.Z{
			Score:  float64(nextRetryTime.Unix()),
			Member: string(data),
		}).Err(); err != nil {
			log.Printf("Failed to add retry to Redis sorted set: %v", err)
		}
	}

	log.Printf("Scheduled retry #%d for notification %s in %d seconds", attempt, notificationID, delay)
	return nil
}

// ProcessDueRetries processes all notifications that are due for retry
func (rm *RetryManager) ProcessDueRetries(ctx context.Context) (int, error) {
	if rm.DB == nil {
		return 0, fmt.Errorf("database not initialized")
	}

	now := time.Now().UnixMilli()
	var notifications []models.Notification

	// Find notifications that are pending and due for send/retry
	err := rm.DB.WithContext(ctx).
		Where("status = ? AND send_at IS NOT NULL AND send_at <= ?", models.StatusPending, now).
		Limit(100). // Process max 100 at a time
		Find(&notifications).Error

	if err != nil {
		return 0, fmt.Errorf("failed to fetch due notifications: %w", err)
	}

	if len(notifications) == 0 {
		return 0, nil
	}

	log.Printf("Processing %d notifications due for retry/send", len(notifications))

	processedCount := 0
	for _, notif := range notifications {
		// Queue the notification for processing
		if rm.RDB != nil {
			notifData, _ := json.Marshal(map[string]string{
				"id":     notif.ID,
				"action": "send",
			})
			if err := rm.RDB.LPush(ctx, "notification:queue", string(notifData)).Err(); err != nil {
				log.Printf("Failed to queue notification %s: %v", notif.ID, err)
				continue
			}
			processedCount++
		}
	}

	return processedCount, nil
}

// CleanupOldRetries removes old retry entries from Redis
func (rm *RetryManager) CleanupOldRetries(ctx context.Context) error {
	if rm.RDB == nil {
		return nil
	}

	// Remove retry entries older than 7 days
	cutoff := time.Now().Add(-7 * 24 * time.Hour).Unix()
	return rm.RDB.ZRemRangeByScore(ctx, "notification:retries", "0", fmt.Sprintf("%d", cutoff)).Err()
}
