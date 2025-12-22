package providers

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"notification_system/models"
)

type TextbeltProvider struct {
	APIKey string
}

func NewTextbeltProvider(apiKey string) *TextbeltProvider {
	if apiKey == "" {
		apiKey = "textbelt"
	}
	return &TextbeltProvider{
		APIKey: apiKey,
	}
}

func (t *TextbeltProvider) ProviderName() string {
	return "textbelt"
}

func (t *TextbeltProvider) Send(ctx context.Context, notification *models.Notification) error {
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

	requestBody := map[string]string{
		"phone":   to,
		"message": body,
		"key":     t.APIKey,
	}

	jsonData, err := json.Marshal(requestBody)
	if err != nil {
		return fmt.Errorf("failed to marshal request: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, "POST", "https://textbelt.com/text", bytes.NewBuffer(jsonData))
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("failed to send SMS: %w", err)
	}
	defer resp.Body.Close()

	responseBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("failed to read response: %w", err)
	}

	var result map[string]interface{}
	if err := json.Unmarshal(responseBody, &result); err != nil {
		return fmt.Errorf("failed to parse response: %w", err)
	}

	success, ok := result["success"].(bool)
	if !ok || !success {
		errorMsg := "unknown error"
		if errStr, ok := result["error"].(string); ok {
			errorMsg = errStr
		}
		return fmt.Errorf("textbelt error: %s", errorMsg)
	}

	notification.Status = models.StatusSent
	now := time.Now().UnixMilli()
	notification.SentAt = &now
	responseStr := string(responseBody)
	notification.ProviderResponse = &responseStr

	return nil
}
