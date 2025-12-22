package models

import "time"

type NotificationPreference struct {
	ID              string      `gorm:"type:char(36);primaryKey"`
	UserID          string      `gorm:"type:char(36);not null;index:idx_user_channel,priority:1"`
	User            Users       `gorm:"constraint:OnUpdate:CASCADE,OnDelete:CASCADE;foreignKey:UserID"`
	Channel         MessageType `gorm:"type:varchar(20);not null;index:idx_user_channel,priority:2"`
	Enabled         bool        `gorm:"not null;default:true;index:idx_preference_enabled"`
	FrequencyCap    *int        `gorm:"type:int"`
	QuietHoursStart *time.Time  `gorm:"type:time"`
	QuietHoursEnd   *time.Time  `gorm:"type:time"`
	Timezone        string      `gorm:"type:varchar(50);not null;default:UTC"`
	CreatedAt       int64       `gorm:"autoCreateTime:milli"`
	UpdatedAt       int64       `gorm:"autoUpdateTime:milli"`
}

