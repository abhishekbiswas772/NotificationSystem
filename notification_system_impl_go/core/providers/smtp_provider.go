package providers

import (
	"context"
	"crypto/tls"
	"encoding/json"
	"fmt"
	"net/smtp"
	"os"
	"time"

	"notification_system/models"
)

type SMTPProvider struct {
	Host     string
	Port     string
	Username string
	Password string
	From     string
}

func NewSMTPProvider(host, port, username, password, from string) *SMTPProvider {
	return &SMTPProvider{
		Host:     host,
		Port:     port,
		Username: username,
		Password: password,
		From:     from,
	}
}

func NewGmailProvider(email, password string) *SMTPProvider {
	return &SMTPProvider{
		Host:     "smtp.gmail.com",
		Port:     "587",
		Username: email,
		Password: password,
		From:     email,
	}
}

func NewOutlookProvider(email, password string) *SMTPProvider {
	return &SMTPProvider{
		Host:     "smtp-mail.outlook.com",
		Port:     "587",
		Username: email,
		Password: password,
		From:     email,
	}
}

func (s *SMTPProvider) ProviderName() string {
	return "smtp"
}

func (s *SMTPProvider) Send(ctx context.Context, notification *models.Notification) error {
	var payload map[string]interface{}
	if err := json.Unmarshal([]byte(notification.Payload), &payload); err != nil {
		return fmt.Errorf("invalid payload: %w", err)
	}

	to, ok := payload["to"].(string)
	if !ok {
		return fmt.Errorf("missing 'to' field in payload")
	}

	subject, ok := payload["subject"].(string)
	if !ok {
		subject = "Notification"
	}

	body, ok := payload["body"].(string)
	if !ok {
		return fmt.Errorf("missing 'body' field in payload")
	}

	from := s.From
	if payloadFrom, ok := payload["from"].(string); ok && payloadFrom != "" {
		from = payloadFrom
	}

	message := fmt.Sprintf("From: %s\r\n", from)
	message += fmt.Sprintf("To: %s\r\n", to)
	message += fmt.Sprintf("Subject: %s\r\n", subject)
	message += fmt.Sprintf("MIME-Version: 1.0\r\n")
	message += fmt.Sprintf("Content-Type: text/html; charset=UTF-8\r\n")
	message += fmt.Sprintf("\r\n%s\r\n", body)

	auth := smtp.PlainAuth("", s.Username, s.Password, s.Host)

	addr := fmt.Sprintf("%s:%s", s.Host, s.Port)

	tlsConfig := &tls.Config{
		InsecureSkipVerify: false,
		ServerName:         s.Host,
	}

	conn, err := smtp.Dial(addr)
	if err != nil {
		return fmt.Errorf("failed to connect to SMTP server: %w", err)
	}
	defer conn.Close()

	if err := conn.StartTLS(tlsConfig); err != nil {
		return fmt.Errorf("failed to start TLS: %w", err)
	}

	if err := conn.Auth(auth); err != nil {
		return fmt.Errorf("SMTP authentication failed: %w", err)
	}

	if err := conn.Mail(from); err != nil {
		return fmt.Errorf("failed to set sender: %w", err)
	}

	if err := conn.Rcpt(to); err != nil {
		return fmt.Errorf("failed to set recipient: %w", err)
	}

	writer, err := conn.Data()
	if err != nil {
		return fmt.Errorf("failed to get data writer: %w", err)
	}

	_, err = writer.Write([]byte(message))
	if err != nil {
		return fmt.Errorf("failed to write message: %w", err)
	}

	if err := writer.Close(); err != nil {
		return fmt.Errorf("failed to close writer: %w", err)
	}

	if err := conn.Quit(); err != nil {
		return fmt.Errorf("failed to quit connection: %w", err)
	}

	notification.Status = models.StatusSent
	now := time.Now().UnixMilli()
	notification.SentAt = &now
	response := fmt.Sprintf("Email sent via SMTP to %s", to)
	notification.ProviderResponse = &response

	return nil
}

func LoadSMTPProviderFromEnv() *SMTPProvider {
	provider := os.Getenv("SMTP_PROVIDER")

	if provider == "gmail" {
		email := os.Getenv("GMAIL_EMAIL")
		password := os.Getenv("GMAIL_APP_PASSWORD")
		return NewGmailProvider(email, password)
	}

	if provider == "outlook" {
		email := os.Getenv("OUTLOOK_EMAIL")
		password := os.Getenv("OUTLOOK_PASSWORD")
		return NewOutlookProvider(email, password)
	}

	return NewSMTPProvider(
		os.Getenv("SMTP_HOST"),
		os.Getenv("SMTP_PORT"),
		os.Getenv("SMTP_USERNAME"),
		os.Getenv("SMTP_PASSWORD"),
		os.Getenv("SMTP_FROM_EMAIL"),
	)
}
