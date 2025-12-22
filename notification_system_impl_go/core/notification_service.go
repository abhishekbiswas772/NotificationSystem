package core

import (
	"context"
	"errors"
	"time"

	"github.com/google/uuid"
	"github.com/redis/go-redis/v9"
	"gorm.io/gorm"
	"gorm.io/gorm/clause"

	"notification_system/models"
)

type NotificationService struct {
	DB  *gorm.DB
	RDB *redis.Client
}

type CreateNotificationInput struct {
	UserID         string
	MessageType    models.MessageType
	Provider       models.ProviderType
	Payload        string
	IdempotencyKey *string
	SendAt         *int64
	MaxRetries     *int
}

type ListNotificationsFilter struct {
	UserID string
	Status *models.NotificationStatus
	Limit  int
	Offset int
}

func (s *NotificationService) CreateNotification(ctx context.Context, input CreateNotificationInput) (*models.Notification, error) {
	if s.DB == nil {
		return nil, errors.New("database not initialized")
	}
	if input.UserID == "" || input.Payload == "" || input.MessageType == "" || input.Provider == "" {
		return nil, errors.New("user_id, payload, message_type, and provider are required")
	}

	notification := &models.Notification{
		ID:             uuid.NewString(),
		UserID:         input.UserID,
		MessageType:    input.MessageType,
		Provider:       input.Provider,
		Status:         models.StatusPending,
		Payload:        input.Payload,
		MaxRetries:     5,
		AttemptCount:   0,
		SendAt:         input.SendAt,
		IdempotencyKey: "",
	}

	if input.MaxRetries != nil {
		notification.MaxRetries = *input.MaxRetries
	}

	if input.IdempotencyKey != nil && *input.IdempotencyKey != "" {
		notification.IdempotencyKey = *input.IdempotencyKey
	} else {
		notification.IdempotencyKey = notification.GenerateIdempotencyKey()
	}

	if s.RDB != nil {
		ctxWithTimeout, cancel := context.WithTimeout(ctx, 2*time.Second)
		defer cancel()
		if notification.IsDuplicate(ctxWithTimeout, s.RDB, 86400) {
			return nil, errors.New("duplicate notification (idempotency)")
		}
	}

	if err := s.DB.WithContext(ctx).Create(notification).Error; err != nil {
		return nil, err
	}

	return notification, nil
}

func (s *NotificationService) BulkCreate(ctx context.Context, inputs []CreateNotificationInput) ([]models.Notification, error) {
	results := make([]models.Notification, 0, len(inputs))
	for _, in := range inputs {
		n, err := s.CreateNotification(ctx, in)
		if err != nil {
			return nil, err
		}
		results = append(results, *n)
	}
	return results, nil
}

func (s *NotificationService) GetNotification(ctx context.Context, id string) (*models.Notification, error) {
	if s.DB == nil {
		return nil, errors.New("database not initialized")
	}
	var notification models.Notification
	if err := s.DB.WithContext(ctx).
		Preload("DLQ").
		Preload("WebhookDeliveries").
		First(&notification, "id = ?", id).Error; err != nil {
		return nil, err
	}
	return &notification, nil
}

func (s *NotificationService) ListNotifications(ctx context.Context, filter ListNotificationsFilter) ([]models.Notification, error) {
	if s.DB == nil {
		return nil, errors.New("database not initialized")
	}
	query := s.DB.WithContext(ctx).Model(&models.Notification{})
	if filter.UserID != "" {
		query = query.Where("user_id = ?", filter.UserID)
	}
	if filter.Status != nil {
		query = query.Where("status = ?", *filter.Status)
	}
	limit := filter.Limit
	if limit <= 0 || limit > 100 {
		limit = 20
	}
	offset := filter.Offset
	if offset < 0 {
		offset = 0
	}
	var notifications []models.Notification
	if err := query.Limit(limit).Offset(offset).Order("created_at DESC").Find(&notifications).Error; err != nil {
		return nil, err
	}
	return notifications, nil
}

func (s *NotificationService) CancelNotification(ctx context.Context, id string) error {
	if s.DB == nil {
		return errors.New("database not initialized")
	}
	return s.DB.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		var notif models.Notification
		if err := tx.Clauses(clause.Locking{Strength: "UPDATE"}).First(&notif, "id = ?", id).Error; err != nil {
			return err
		}
		if notif.Status != models.StatusPending {
			return errors.New("only pending notifications can be cancelled")
		}
		if err := tx.Model(&notif).Updates(map[string]interface{}{
			"status":    models.StatusCancelled,
			"failed_at": time.Now().UnixMilli(),
		}).Error; err != nil {
			return err
		}
		return nil
	})
}
