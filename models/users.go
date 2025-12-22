package models

import (
	"errors"
	"notification_system/configs"
)

type Users struct {
	ID            string                   `gorm:"type:char(36);primaryKey"`
	Email         string                   `gorm:"type:varchar(255);uniqueIndex;not null"`
	Username      string                   `gorm:"type:varchar(100);uniqueIndex;not null"`
	CreatedAt     int64                    `gorm:"autoCreateTime:milli"`
	UpdatedAt     int64                    `gorm:"autoUpdateTime:milli"`
	Notifications []Notification           `gorm:"constraint:OnUpdate:CASCADE,OnDelete:CASCADE;foreignKey:UserID"`
	Preferences   []NotificationPreference `gorm:"constraint:OnUpdate:CASCADE,OnDelete:CASCADE;foreignKey:UserID"`
	Webhooks      []NotificationWebhook    `gorm:"constraint:OnUpdate:CASCADE,OnDelete:CASCADE;foreignKey:UserID"`
	APIKeys       []APIKey                 `gorm:"constraint:OnUpdate:CASCADE,OnDelete:CASCADE;foreignKey:UserID"`
	RateLimits    []RateLimit              `gorm:"constraint:OnUpdate:CASCADE,OnDelete:CASCADE;foreignKey:UserID"`
	AuditLogs     []AuditLog               `gorm:"constraint:OnUpdate:CASCADE,OnDelete:SET NULL;foreignKey:UserID"`
	Templates     []NotificationTemplate   `gorm:"constraint:OnUpdate:CASCADE,OnDelete:SET NULL;foreignKey:CreatedBy"`
}

func (user *Users) CreateUsers() (*Users, error) {
	if user == nil {
		return nil, errors.New("user cannot be nil")
	}

	db := configs.DB
	if db == nil {
		configs.ConnectDatabase()
		db = configs.DB
		if db == nil {
			return nil, errors.New("database connection failed")
		}
	}

	result := db.Create(&user)
	if result.Error != nil {
		return nil, result.Error
	}

	return user, nil
}
