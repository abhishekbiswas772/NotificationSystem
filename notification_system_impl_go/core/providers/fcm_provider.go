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

type FCMProvider struct {
	ServerKey string
}

func NewFCMProvider(serverKey string) *FCMProvider {
	return &FCMProvider{
		ServerKey: serverKey,
	}
}

func (f *FCMProvider) ProviderName() string {
	return "fcm"
}

func (f *FCMProvider) Send(ctx context.Context, notification *models.Notification) error {
	var payload map[string]interface{}
	if err := json.Unmarshal([]byte(notification.Payload), &payload); err != nil {
		return fmt.Errorf("invalid payload: %w", err)
	}

	token, hasToken := payload["token"].(string)
	topic, hasTopic := payload["topic"].(string)

	if !hasToken && !hasTopic {
		return fmt.Errorf("missing 'token' or 'topic' field in payload")
	}

	fcmMessage := map[string]interface{}{
		"notification": map[string]interface{}{
			"title": payload["title"],
			"body":  payload["body"],
		},
	}

	if data, ok := payload["data"].(map[string]interface{}); ok {
		fcmMessage["data"] = data
	}

	if hasToken {
		fcmMessage["to"] = token
	} else {
		fcmMessage["to"] = "/topics/" + topic
	}

	jsonData, err := json.Marshal(fcmMessage)
	if err != nil {
		return fmt.Errorf("failed to marshal FCM message: %w", err)
	}

	req, err := http.NewRequestWithContext(
		ctx,
		"POST",
		"https://fcm.googleapis.com/fcm/send",
		bytes.NewBuffer(jsonData),
	)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "key="+f.ServerKey)

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("failed to send FCM notification: %w", err)
	}
	defer resp.Body.Close()

	responseBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode >= 400 {
		return fmt.Errorf("FCM returned error status %d: %s", resp.StatusCode, string(responseBody))
	}

	var result map[string]interface{}
	if err := json.Unmarshal(responseBody, &result); err != nil {
		return fmt.Errorf("failed to parse response: %w", err)
	}

	if success, ok := result["success"].(float64); ok && success > 0 {
		notification.Status = models.StatusSent
		now := time.Now().UnixMilli()
		notification.SentAt = &now
		responseStr := string(responseBody)
		notification.ProviderResponse = &responseStr
		return nil
	}

	if failure, ok := result["failure"].(float64); ok && failure > 0 {
		errorMsg := "FCM send failed"
		if results, ok := result["results"].([]interface{}); ok && len(results) > 0 {
			if firstResult, ok := results[0].(map[string]interface{}); ok {
				if err, ok := firstResult["error"].(string); ok {
					errorMsg = err
				}
			}
		}
		return fmt.Errorf("FCM error: %s", errorMsg)
	}

	return fmt.Errorf("unexpected FCM response: %s", string(responseBody))
}
