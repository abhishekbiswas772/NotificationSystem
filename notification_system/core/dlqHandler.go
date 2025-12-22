package core

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"time"

	"github.com/google/uuid"
	"gorm.io/gorm"

	"notification_system/models"
)

type DLQManager struct {
	DB *gorm.DB
}

// MoveToDLQ moves a failed notification to the Dead Letter Queue
func (dlq *DLQManager) MoveToDLQ(ctx context.Context, notificationID string, reason string, errorDetails string) error {
	if dlq.DB == nil {
		return fmt.Errorf("database not initialized")
	}

	return dlq.DB.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		// Get the notification
		var notification models.Notification
		if err := tx.First(&notification, "id = ?", notificationID).Error; err != nil {
			return fmt.Errorf("notification not found: %w", err)
		}

		// Build retry history
		retryHistory := map[string]interface{}{
			"total_attempts": notification.AttemptCount,
			"last_error":     errorDetails,
			"last_attempted": notification.LastAttempted,
			"failure_reason": reason,
		}
		historyJSON, _ := json.Marshal(retryHistory)
		historyStr := string(historyJSON)

		// Create DLQ entry
		dlqEntry := models.NotificationDLQ{
			ID:             uuid.NewString(),
			NotificationID: notificationID,
			FailureReason:  reason,
			RetryHistory:   &historyStr,
			Resolved:       false,
		}

		if err := tx.Create(&dlqEntry).Error; err != nil {
			return fmt.Errorf("failed to create DLQ entry: %w", err)
		}

		// Update notification status
		now := time.Now().UnixMilli()
		updates := map[string]interface{}{
			"status":    models.StatusFailed,
			"failed_at": now,
		}

		if err := tx.Model(&notification).Updates(updates).Error; err != nil {
			return fmt.Errorf("failed to update notification status: %w", err)
		}

		log.Printf("Moved notification %s to DLQ with reason: %s", notificationID, reason)
		return nil
	})
}

// RetryFromDLQ retries a notification from the DLQ
func (dlq *DLQManager) RetryFromDLQ(ctx context.Context, dlqID string) error {
	if dlq.DB == nil {
		return fmt.Errorf("database not initialized")
	}

	return dlq.DB.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		// Get DLQ entry
		var dlqEntry models.NotificationDLQ
		if err := tx.First(&dlqEntry, "id = ?", dlqID).Error; err != nil {
			return fmt.Errorf("DLQ entry not found: %w", err)
		}

		if dlqEntry.Resolved {
			return fmt.Errorf("DLQ entry already resolved")
		}

		// Get the notification
		var notification models.Notification
		if err := tx.First(&notification, "id = ?", dlqEntry.NotificationID).Error; err != nil {
			return fmt.Errorf("notification not found: %w", err)
		}

		// Reset notification for retry
		updates := map[string]interface{}{
			"status":        models.StatusPending,
			"attempt_count": 0,
			"failed_at":     nil,
			"error_message": nil,
			"send_at":       time.Now().UnixMilli(),
		}

		if err := tx.Model(&notification).Updates(updates).Error; err != nil {
			return fmt.Errorf("failed to update notification: %w", err)
		}

		log.Printf("Retrying notification %s from DLQ entry %s", notification.ID, dlqID)
		return nil
	})
}

// ResolveDLQEntry marks a DLQ entry as resolved
func (dlq *DLQManager) ResolveDLQEntry(ctx context.Context, dlqID string, resolvedBy *string, note string) error {
	if dlq.DB == nil {
		return fmt.Errorf("database not initialized")
	}

	now := time.Now().UnixMilli()
	updates := map[string]interface{}{
		"resolved":    true,
		"resolved_at": now,
	}

	if resolvedBy != nil {
		updates["resolved_by"] = *resolvedBy
	}

	if err := dlq.DB.WithContext(ctx).Model(&models.NotificationDLQ{}).
		Where("id = ?", dlqID).
		Updates(updates).Error; err != nil {
		return fmt.Errorf("failed to resolve DLQ entry: %w", err)
	}

	log.Printf("Resolved DLQ entry %s", dlqID)
	return nil
}

// ListDLQEntries retrieves DLQ entries with optional filtering
func (dlq *DLQManager) ListDLQEntries(ctx context.Context, resolved *bool, limit, offset int) ([]models.NotificationDLQ, error) {
	if dlq.DB == nil {
		return nil, fmt.Errorf("database not initialized")
	}

	query := dlq.DB.WithContext(ctx).Model(&models.NotificationDLQ{})

	if resolved != nil {
		query = query.Where("resolved = ?", *resolved)
	}

	if limit <= 0 || limit > 100 {
		limit = 20
	}

	var entries []models.NotificationDLQ
	if err := query.Preload("Notification").
		Limit(limit).
		Offset(offset).
		Order("moved_to_dlq_at DESC").
		Find(&entries).Error; err != nil {
		return nil, fmt.Errorf("failed to fetch DLQ entries: %w", err)
	}

	return entries, nil
}

// CleanupOldDLQEntries removes resolved DLQ entries older than specified days
func (dlq *DLQManager) CleanupOldDLQEntries(ctx context.Context, daysOld int) (int64, error) {
	if dlq.DB == nil {
		return 0, fmt.Errorf("database not initialized")
	}

	cutoffTime := time.Now().Add(-time.Duration(daysOld) * 24 * time.Hour).UnixMilli()

	result := dlq.DB.WithContext(ctx).
		Where("resolved = ? AND resolved_at < ?", true, cutoffTime).
		Delete(&models.NotificationDLQ{})

	if result.Error != nil {
		return 0, fmt.Errorf("failed to cleanup old DLQ entries: %w", result.Error)
	}

	log.Printf("Cleaned up %d old DLQ entries (older than %d days)", result.RowsAffected, daysOld)
	return result.RowsAffected, nil
}

// GetDLQStats returns statistics about the DLQ
func (dlq *DLQManager) GetDLQStats(ctx context.Context) (map[string]interface{}, error) {
	if dlq.DB == nil {
		return nil, fmt.Errorf("database not initialized")
	}

	var totalCount, unresolvedCount int64

	if err := dlq.DB.WithContext(ctx).Model(&models.NotificationDLQ{}).Count(&totalCount).Error; err != nil {
		return nil, err
	}

	if err := dlq.DB.WithContext(ctx).Model(&models.NotificationDLQ{}).
		Where("resolved = ?", false).
		Count(&unresolvedCount).Error; err != nil {
		return nil, err
	}

	return map[string]interface{}{
		"total_entries":      totalCount,
		"unresolved_entries": unresolvedCount,
		"resolved_entries":   totalCount - unresolvedCount,
	}, nil
}
