package models

type ProviderConfig struct {
	ID             string  `gorm:"type:char(36);primaryKey"`
	ProviderName   string  `gorm:"type:varchar(50);not null;uniqueIndex:idx_provider_name"`
	APIKey         string  `gorm:"type:varchar(255);not null"`
	APISecret      *string `gorm:"type:varchar(255)"`
	ConfigJSON     *string `gorm:"type:text"`
	IsActive       bool    `gorm:"not null;default:true;index:idx_provider_active"`
	RateLimit      *int
	TimeoutSeconds int   `gorm:"not null;default:30"`
	Priority       int   `gorm:"not null;default:0;index:idx_provider_priority"`
	CreatedAt      int64 `gorm:"autoCreateTime:milli"`
	UpdatedAt      int64 `gorm:"autoUpdateTime:milli"`
}

func (ProviderConfig) TableName() string {
	return "provider_configs"
}
