package models

type WebhookDelivery struct {
	ID             string `gorm:"type:char(36);primaryKey"`
	WebhookID      string `gorm:"type:char(36);not null;index:idx_webhook_delivery,priority:1"`
	NotificationID string `gorm:"type:char(36);not null;index:idx_webhook_delivery,priority:2"`
	EventType      string `gorm:"type:varchar(50);not null"`
	Payload        string `gorm:"type:text;not null"`
	ResponseStatus *int
	ResponseBody   *string `gorm:"type:text"`
	AttemptCount   int     `gorm:"not null;default:1"`
	Delivered      bool    `gorm:"not null;default:false;index:idx_delivery_status"`
	DeliveredAt    *int64
	CreatedAt      int64               `gorm:"autoCreateTime:milli"`
	UpdatedAt      int64               `gorm:"autoUpdateTime:milli"`
	NextRetryAt    *int64              `gorm:"index:idx_next_retry"`
	Webhook        NotificationWebhook `gorm:"constraint:OnUpdate:CASCADE,OnDelete:CASCADE;foreignKey:WebhookID"`
	Notification   Notification        `gorm:"constraint:OnUpdate:CASCADE,OnDelete:CASCADE;foreignKey:NotificationID"`
}

func (WebhookDelivery) TableName() string {
	return "webhook_deliveries"
}
