package models

type APIKey struct {
	ID         string  `gorm:"type:char(36);primaryKey"`
	UserID     string  `gorm:"type:char(36);not null;index:idx_api_key_user"`
	User       *Users  `gorm:"constraint:OnUpdate:CASCADE,OnDelete:CASCADE;foreignKey:UserID"`
	KeyHash    string  `gorm:"type:varchar(64);not null;uniqueIndex:idx_api_key_hash"`
	Name       string  `gorm:"type:varchar(100);not null"`
	Scopes     *string `gorm:"type:text"`
	IsActive   bool    `gorm:"not null;default:true;index:idx_api_key_active"`
	ExpiresAt  *int64
	LastUsedAt *int64
	CreatedAt  int64 `gorm:"autoCreateTime:milli"`
	UpdatedAt  int64 `gorm:"autoUpdateTime:milli"`
}

func (APIKey) TableName() string {
	return "api_keys"
}
