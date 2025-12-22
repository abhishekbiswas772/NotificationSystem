package core

import (
	"context"
	"errors"
	"log"
	"time"
	"notification_system/models"
)

type NotificationProvider interface {
	Send(ctx context.Context, notification *models.Notification) error
	ProviderName() string
}

type MockProvider struct{}

func (m MockProvider) ProviderName() string {
	return "mock"
}

func (m MockProvider) Send(ctx context.Context, notification *models.Notification) error {
	if notification == nil {
		return errors.New("nil notification")
	}
	log.Printf("[MOCK] send notification %s to user %s via %s", notification.ID, notification.UserID, notification.Provider)
	notification.Status = models.StatusSent
	now := time.Now().UnixMilli()
	notification.SentAt = &now
	return nil
}
