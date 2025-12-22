package providers

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"time"
	"notification_system/models"
)

type ConsoleSMSProvider struct{}

func NewConsoleSMSProvider() *ConsoleSMSProvider {
	return &ConsoleSMSProvider{}
}

func (c *ConsoleSMSProvider) ProviderName() string {
	return "console_sms"
}

func (c *ConsoleSMSProvider) Send(ctx context.Context, notification *models.Notification) error {
	var payload map[string]interface{}
	if err := json.Unmarshal([]byte(notification.Payload), &payload); err != nil {
		return fmt.Errorf("invalid payload: %w", err)
	}

	to, ok := payload["to"].(string)
	if !ok {
		return fmt.Errorf("missing 'to' field in payload")
	}

	body, ok := payload["body"].(string)
	if !ok {
		return fmt.Errorf("missing 'body' field in payload")
	}

	fmt.Println()
	fmt.Println("═══════════════════════════════════════════════════════")
	fmt.Println("📱 SMS NOTIFICATION")
	fmt.Println("═══════════════════════════════════════════════════════")
	fmt.Printf("To:      %s\n", to)
	fmt.Printf("Message: %s\n", body)
	fmt.Printf("Time:    %s\n", time.Now().Format("2006-01-02 15:04:05"))
	fmt.Println("═══════════════════════════════════════════════════════")
	fmt.Println()

	log.Printf("[SMS] To: %s | Message: %s", to, body)

	notification.Status = models.StatusSent
	now := time.Now().UnixMilli()
	notification.SentAt = &now
	response := fmt.Sprintf("SMS logged to console for %s", to)
	notification.ProviderResponse = &response

	return nil
}
