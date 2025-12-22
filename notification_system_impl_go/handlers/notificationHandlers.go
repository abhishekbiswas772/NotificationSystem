package handlers

import (
	"net/http"
	"strconv"
	"github.com/gin-gonic/gin"
	"notification_system/core"
	"notification_system/models"
)

type NotificationHandler struct {
	Service *core.NotificationService
}

type createNotificationRequest struct {
	UserID         string              `json:"user_id" binding:"required"`
	MessageType    models.MessageType  `json:"message_type" binding:"required"`
	Provider       models.ProviderType `json:"provider" binding:"required"`
	Payload        string              `json:"payload" binding:"required"`
	IdempotencyKey *string             `json:"idempotency_key"`
	SendAt         *int64              `json:"send_at"`
	MaxRetries     *int                `json:"max_retries"`
}

func (h *NotificationHandler) RegisterRoutes(rg *gin.RouterGroup) {
	rg.POST("/notifications", h.createNotification)
	rg.POST("/notifications/bulk", h.bulkCreate)
	rg.GET("/notifications/:id", h.getNotification)
	rg.GET("/notifications", h.listNotifications)
	rg.DELETE("/notifications/:id", h.cancelNotification)
}

func (h *NotificationHandler) createNotification(ctx *gin.Context) {
	var req createNotificationRequest
	if err := ctx.ShouldBindJSON(&req); err != nil {
		ctx.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	notification, err := h.Service.CreateNotification(ctx, core.CreateNotificationInput{
		UserID:         req.UserID,
		MessageType:    req.MessageType,
		Provider:       req.Provider,
		Payload:        req.Payload,
		IdempotencyKey: req.IdempotencyKey,
		SendAt:         req.SendAt,
		MaxRetries:     req.MaxRetries,
	})
	if err != nil {
		ctx.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	ctx.JSON(http.StatusCreated, gin.H{"notification": notification})
}

func (h *NotificationHandler) bulkCreate(ctx *gin.Context) {
	var req []createNotificationRequest
	if err := ctx.ShouldBindJSON(&req); err != nil {
		ctx.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	inputs := make([]core.CreateNotificationInput, 0, len(req))
	for _, r := range req {
		inputs = append(inputs, core.CreateNotificationInput{
			UserID:         r.UserID,
			MessageType:    r.MessageType,
			Provider:       r.Provider,
			Payload:        r.Payload,
			IdempotencyKey: r.IdempotencyKey,
			SendAt:         r.SendAt,
			MaxRetries:     r.MaxRetries,
		})
	}
	notifs, err := h.Service.BulkCreate(ctx, inputs)
	if err != nil {
		ctx.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	ctx.JSON(http.StatusCreated, gin.H{"notifications": notifs})
}

func (h *NotificationHandler) getNotification(ctx *gin.Context) {
	id := ctx.Param("id")
	notification, err := h.Service.GetNotification(ctx, id)
	if err != nil {
		ctx.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
		return
	}
	ctx.JSON(http.StatusOK, gin.H{"notification": notification})
}

func (h *NotificationHandler) listNotifications(ctx *gin.Context) {
	limit, _ := strconv.Atoi(ctx.DefaultQuery("limit", "20"))
	offset, _ := strconv.Atoi(ctx.DefaultQuery("offset", "0"))
	statusParam := ctx.Query("status")
	var status *models.NotificationStatus
	if statusParam != "" {
		s := models.NotificationStatus(statusParam)
		status = &s
	}
	filter := core.ListNotificationsFilter{
		UserID: ctx.Query("user_id"),
		Status: status,
		Limit:  limit,
		Offset: offset,
	}
	notifications, err := h.Service.ListNotifications(ctx, filter)
	if err != nil {
		ctx.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	ctx.JSON(http.StatusOK, gin.H{"notifications": notifications})
}

func (h *NotificationHandler) cancelNotification(ctx *gin.Context) {
	id := ctx.Param("id")
	if err := h.Service.CancelNotification(ctx, id); err != nil {
		ctx.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	ctx.JSON(http.StatusOK, gin.H{"status": "cancelled"})
}
