package models

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"log"
	"time"

	"github.com/redis/go-redis/v9"
)

type MessageType string
type ProviderType string
type NotificationStatus string

const (
	SMS   MessageType = "sms"
	EMAIL MessageType = "email"
	PUSH  MessageType = "push"
)

const (
	GMAIL       ProviderType = "gmail"
	OUTLOOK     ProviderType = "outlook"
	CUSTOMSMTP  ProviderType = "custom_smtp"
	TEXTBELT    ProviderType = "textbelt"
	CONSOLESMS  ProviderType = "console_sms"
	FCM         ProviderType = "fcm"
	LOCAL       ProviderType = "local"
)

const (
	StatusPending   NotificationStatus = "pending"
	StatusSent      NotificationStatus = "sent"
	StatusFailed    NotificationStatus = "failed"
	StatusCancelled NotificationStatus = "cancelled"
)

type Notification struct {
	ID                string             `gorm:"type:char(36);primaryKey"`
	UserID            string             `gorm:"type:char(36);not null;index:idx_user_type,priority:1;index:idx_user_status,priority:1"`
	IdempotencyKey    string             `gorm:"type:varchar(64);not null;uniqueIndex:idx_idempotency"`
	MessageType       MessageType        `gorm:"type:varchar(20);not null;index:idx_user_type,priority:2"`
	Provider          ProviderType       `gorm:"type:varchar(20);not null"`
	Status            NotificationStatus `gorm:"type:varchar(20);not null;default:pending;index:idx_status_created,priority:1;index:idx_user_status,priority:2"`
	Payload           string             `gorm:"type:text;not null"`
	AttemptCount      int                `gorm:"not null;default:0"`
	MaxRetries        int                `gorm:"not null;default:5"`
	CreatedAt         int64              `gorm:"index:idx_status_created,priority:2;autoCreateTime:milli"`
	UpdatedAt         int64              `gorm:"autoUpdateTime:milli"`
	LastAttempted     *int64
	SendAt            *int64  `gorm:"index:idx_send_at"`
	FailedAt          *int64
	SentAt            *int64
	ErrorMessage      *string `gorm:"type:text"`
	ProviderResponse  *string `gorm:"type:text"`
	User              Users   `gorm:"constraint:OnUpdate:CASCADE,OnDelete:CASCADE;foreignKey:UserID;references:ID"`
	DLQ               *NotificationDLQ  `gorm:"constraint:OnUpdate:CASCADE,OnDelete:CASCADE;foreignKey:NotificationID;references:ID"`
	WebhookDeliveries []WebhookDelivery `gorm:"constraint:OnUpdate:CASCADE,OnDelete:CASCADE;foreignKey:NotificationID;references:ID"`
}

type NotificationDLQ struct {
	ID             string  `gorm:"type:char(36);primaryKey"`
	NotificationID string  `gorm:"type:char(36);not null;uniqueIndex:idx_notification_dlq"`
	FailureReason  string  `gorm:"type:text;not null"`
	RetryHistory   *string `gorm:"type:text"`
	MovedToDlqAt   int64   `gorm:"autoCreateTime:milli;index:idx_moved_at"`
	Resolved       bool    `gorm:"not null;default:false;index:idx_resolved"`
	ResolvedAt     *int64
	ResolvedBy     *string      `gorm:"type:char(36)"`
	Notification   Notification `gorm:"constraint:OnUpdate:CASCADE,OnDelete:CASCADE;foreignKey:NotificationID"`
	Resolver       *Users       `gorm:"constraint:OnUpdate:CASCADE,OnDelete:SET NULL;foreignKey:ResolvedBy"`
}

func (Notification) TableName() string {
	return "notifications"
}

func (NotificationDLQ) TableName() string {
	return "notification_dlq"
}

func (n *Notification) GenerateIdempotencyKey() string {
	content := fmt.Sprintf("%s:%s:%s:%d",
		n.UserID,
		n.MessageType,
		n.Payload,
		time.Now().Unix(),
	)
	hash256 := sha256.Sum256([]byte(content))
	return hex.EncodeToString(hash256[:])
}

func (n *Notification) IsDuplicate(ctx context.Context, rdb *redis.Client, ttl int) bool {
	if ttl <= 0 {
		ttl = 86400
	}

	idempotencyKey := n.GenerateIdempotencyKey()
	key := fmt.Sprintf("notif:sent:%s", idempotencyKey)

	if rdb == nil {
		log.Println("redis client not found")
		return false
	}

	ok, err := rdb.SetNX(ctx, key, "1", time.Duration(ttl)*time.Second).Result()
	if err != nil {
		log.Printf("unable to save in redis: %v", err)
		return false
	}
	return !ok
}
