package models

type ResourceType string
type ActionType string

const (
	ResourceNotification ResourceType = "notification"
	ResourceUser         ResourceType = "user"
	ResourceWebhook      ResourceType = "webhook"
)

const (
	ActionCreate ActionType = "create"
	ActionUpdate ActionType = "update"
	ActionDelete ActionType = "delete"
)

type AuditLog struct {
	ID           string       `gorm:"type:char(36);primaryKey"`
	UserID       *string      `gorm:"type:char(36);index:idx_audit_user"`
	User         *Users       `gorm:"constraint:OnUpdate:CASCADE,OnDelete:SET NULL;foreignKey:UserID"`
	Action       ActionType   `gorm:"type:varchar(100);not null;index:idx_audit_action"`
	ResourceType ResourceType `gorm:"type:varchar(50);not null;index:idx_audit_resource,priority:1"`
	ResourceID   *string      `gorm:"type:char(36);index:idx_audit_resource,priority:2"`
	IPAddress    *string      `gorm:"type:varchar(45)"`
	UserAgent    *string      `gorm:"type:text"`
	Changes      *string      `gorm:"type:text"`
	CreatedAt    int64        `gorm:"autoCreateTime:milli;index:idx_audit_created"`
	UpdatedAt    int64        `gorm:"autoUpdateTime:milli"`
}

func (AuditLog) TableName() string {
	return "audit_logs"
}
