package providers

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"notification_system/models"
)

type LocalProvider struct{}

func NewLocalProvider() *LocalProvider {
	return &LocalProvider{}
}

func (l *LocalProvider) ProviderName() string {
	return "local"
}

func (l *LocalProvider) Send(ctx context.Context, notification *models.Notification) error {
	var payload map[string]interface{}
	if err := json.Unmarshal([]byte(notification.Payload), &payload); err != nil {
		return fmt.Errorf("invalid payload: %w", err)
	}

	fmt.Println()
	fmt.Println("═══════════════════════════════════════════════════════")
	fmt.Printf("📧 LOCAL NOTIFICATION - %s\n", notification.MessageType)
	fmt.Println("═══════════════════════════════════════════════════════")
	fmt.Printf("Notification ID: %s\n", notification.ID)
	fmt.Printf("User ID:         %s\n", notification.UserID)
	fmt.Printf("Type:            %s\n", notification.MessageType)
	fmt.Printf("Provider:        %s\n", notification.Provider)
	fmt.Printf("Time:            %s\n", time.Now().Format("2006-01-02 15:04:05"))
	fmt.Println("-------------------------------------------------------")

	for key, value := range payload {
		if key == "body" {
			bodyStr := fmt.Sprintf("%v", value)
			if len(bodyStr) > 100 {
				fmt.Printf("%s: %s...\n", key, bodyStr[:100])
			} else {
				fmt.Printf("%s: %v\n", key, value)
			}
		} else {
			fmt.Printf("%s: %v\n", key, value)
		}
	}

	fmt.Println("═══════════════════════════════════════════════════════")
	fmt.Println()

	notification.Status = models.StatusSent
	now := time.Now().UnixMilli()
	notification.SentAt = &now
	response := "Notification logged locally"
	notification.ProviderResponse = &response

	return nil
}
