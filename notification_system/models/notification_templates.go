package models

type NotificationTemplate struct {
	ID          string      `gorm:"type:char(36);primaryKey"`
	Name        string      `gorm:"type:varchar(100);not null;uniqueIndex:idx_template_name"`
	MessageType MessageType `gorm:"type:varchar(20);not null;index:idx_template_type"`
	Subject     *string     `gorm:"type:varchar(255)"`
	Body        string      `gorm:"type:text;not null"`
	Variables   *string     `gorm:"type:text"`
	IsActive    bool        `gorm:"not null;default:true;index:idx_template_active"`
	CreatedBy   *string     `gorm:"type:char(36)"`
	Creator     *Users      `gorm:"constraint:OnUpdate:CASCADE,OnDelete:SET NULL;foreignKey:CreatedBy"`
	CreatedAt   int64       `gorm:"autoCreateTime:milli"`
	UpdatedAt   int64       `gorm:"autoUpdateTime:milli"`
}

