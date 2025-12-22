package models

type RateLimit struct {
	ID           string `gorm:"type:char(36);primaryKey"`
	UserID       string `gorm:"type:char(36);not null;uniqueIndex:idx_rate_limit_user_window,priority:1"`
	User         Users  `gorm:"constraint:OnUpdate:CASCADE,OnDelete:CASCADE;foreignKey:UserID"`
	WindowStart  int64  `gorm:"not null;uniqueIndex:idx_rate_limit_user_window,priority:2"`
	RequestCount int    `gorm:"not null;default:0"`
	LimitType    string `gorm:"type:varchar(20);not null;uniqueIndex:idx_rate_limit_user_window,priority:3"`
	CreatedAt    int64  `gorm:"autoCreateTime:milli"`
	UpdatedAt    int64  `gorm:"autoUpdateTime:milli"`
}

