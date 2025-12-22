package models

import "time"

type NotificationMetric struct {
	ID            string      `gorm:"type:char(36);primaryKey"`
	Date          time.Time   `gorm:"type:date;not null;index:idx_metrics_date,priority:1"`
	Hour          *int        `gorm:"index:idx_metrics_date,priority:2"`
	Provider      string      `gorm:"type:varchar(20);not null;index:idx_metrics_provider"`
	MessageType   MessageType `gorm:"type:varchar(20);not null;index:idx_metrics_type"`
	TotalSent     int         `gorm:"not null;default:0"`
	TotalFailed   int         `gorm:"not null;default:0"`
	TotalPending  int         `gorm:"not null;default:0"`
	AvgDeliveryMs *int64
	CreatedAt     int64 `gorm:"autoCreateTime:milli"`
}
