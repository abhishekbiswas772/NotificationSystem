package providers

import (
	"context"
	"log"
	"os"

	"notification_system/models"
)

type NotificationProvider interface {
	Send(ctx context.Context, notification *models.Notification) error
	ProviderName() string
}

func GetProviderMap() map[models.ProviderType]NotificationProvider {
	providers := make(map[models.ProviderType]NotificationProvider)

	smtpProvider := os.Getenv("SMTP_PROVIDER")

	if smtpProvider == "gmail" {
		email := os.Getenv("GMAIL_EMAIL")
		password := os.Getenv("GMAIL_APP_PASSWORD")
		if email != "" && password != "" {
			log.Println("✓ Using Gmail SMTP for email notifications")
			providers[models.GMAIL] = NewGmailProvider(email, password)
		} else {
			log.Println("⚠ Gmail credentials not found, using mock provider")
		}
	} else if smtpProvider == "outlook" {
		email := os.Getenv("OUTLOOK_EMAIL")
		password := os.Getenv("OUTLOOK_PASSWORD")
		if email != "" && password != "" {
			log.Println("✓ Using Outlook SMTP for email notifications")
			providers[models.OUTLOOK] = NewOutlookProvider(email, password)
		} else {
			log.Println("⚠ Outlook credentials not found, using mock provider")
		}
	} else if smtpProvider == "custom" {
		host := os.Getenv("SMTP_HOST")
		port := os.Getenv("SMTP_PORT")
		username := os.Getenv("SMTP_USERNAME")
		password := os.Getenv("SMTP_PASSWORD")
		from := os.Getenv("SMTP_FROM_EMAIL")
		if host != "" && port != "" && username != "" && password != "" {
			log.Printf("✓ Using custom SMTP (%s:%s) for email notifications", host, port)
			providers[models.CUSTOMSMTP] = NewSMTPProvider(host, port, username, password, from)
		} else {
			log.Println("⚠ Custom SMTP credentials not found, using mock provider")
		}
	}

	smsProvider := os.Getenv("SMS_PROVIDER")

	if smsProvider == "console" {
		log.Println("✓ Using Console SMS provider (logs to terminal)")
		providers[models.CONSOLESMS] = NewConsoleSMSProvider()
	} else if smsProvider == "textbelt" {
		apiKey := os.Getenv("TEXTBELT_API_KEY")
		if apiKey == "" {
			apiKey = "textbelt"
		}
		log.Println("✓ Using Textbelt for SMS notifications (1 free SMS/day)")
		providers[models.TEXTBELT] = NewTextbeltProvider(apiKey)
	}

	fcmKey := os.Getenv("FCM_SERVER_KEY")
	if fcmKey != "" {
		log.Println("✓ Using Firebase FCM for push notifications")
		providers[models.FCM] = NewFCMProvider(fcmKey)
	} else {
		log.Println("⚠ FCM server key not found, using mock provider")
	}

	if providers[models.GMAIL] == nil && providers[models.OUTLOOK] == nil && providers[models.CUSTOMSMTP] == nil {
		log.Println("ℹ Using local provider for email (configure SMTP_PROVIDER in .env)")
		providers[models.LOCAL] = NewLocalProvider()
	}

	if providers[models.CONSOLESMS] == nil && providers[models.TEXTBELT] == nil {
		log.Println("ℹ Using console SMS provider (configure SMS_PROVIDER in .env)")
		providers[models.CONSOLESMS] = NewConsoleSMSProvider()
	}

	if providers[models.FCM] == nil {
		log.Println("ℹ Using local provider for push (configure FCM_SERVER_KEY in .env)")
		providers[models.FCM] = NewLocalProvider()
	}

	return providers
}

func ValidateProviderConfiguration() error {
	smtpProvider := os.Getenv("SMTP_PROVIDER")
	if smtpProvider == "gmail" {
		if os.Getenv("GMAIL_EMAIL") == "" || os.Getenv("GMAIL_APP_PASSWORD") == "" {
			log.Println("⚠ Warning: Gmail SMTP configured but credentials missing")
		}
	}

	smsProvider := os.Getenv("SMS_PROVIDER")
	if smsProvider == "textbelt" {
		log.Println("ℹ Note: Textbelt free tier allows 1 SMS per day")
	}

	if os.Getenv("FCM_SERVER_KEY") == "" {
		log.Println("ℹ Note: FCM not configured. Push notifications will use mock provider")
	}

	return nil
}
