package models

type NotificationWebhook struct {
	ID               string            `gorm:"type:char(36);primaryKey"`
	UserID           string            `gorm:"type:char(36);not null;index:idx_webhook_user"`
	User             Users             `gorm:"constraint:OnUpdate:CASCADE,OnDelete:CASCADE;foreignKey:UserID"`
	URL              string            `gorm:"type:varchar(500);not null"`
	SecretKey        string            `gorm:"type:varchar(64);not null"`
	Events           string            `gorm:"type:text;not null"`
	IsActive         bool              `gorm:"not null;default:true;index:idx_webhook_active"`
	RetryCount       int               `gorm:"not null;default:3"`
	TimeoutSeconds   int               `gorm:"not null;default:10"`
	CreatedAt        int64             `gorm:"autoCreateTime:milli"`
	UpdatedAt        int64             `gorm:"autoUpdateTime:milli"`
	WebhookDeliveries []WebhookDelivery `gorm:"constraint:OnUpdate:CASCADE,OnDelete:CASCADE;foreignKey:WebhookID"`
}

func (NotificationWebhook) TableName() string {
	return "notification_webhooks"
}
