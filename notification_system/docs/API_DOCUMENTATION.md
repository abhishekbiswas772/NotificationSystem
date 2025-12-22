# Notification System API Documentation

## Base URL
```
http://localhost:8080/api/v1
```

## Authentication
All API requests require authentication using one of the following methods:

### 1. API Key (Recommended)
```bash
-H "X-API-Key: your-api-key-here"
```

### 2. JWT Token
```bash
-H "Authorization: Bearer your-jwt-token"
```

---

## Table of Contents
1. [Authentication Endpoints](#authentication-endpoints)
2. [Notification Endpoints](#notification-endpoints)
3. [User Endpoints](#user-endpoints)
4. [Template Endpoints](#template-endpoints)
5. [Webhook Endpoints](#webhook-endpoints)
6. [Preference Endpoints](#preference-endpoints)
7. [Analytics Endpoints](#analytics-endpoints)
8. [DLQ Management Endpoints](#dlq-management-endpoints)
9. [Health Check Endpoints](#health-check-endpoints)

---

## Authentication Endpoints

### Register New User
```bash
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "johndoe",
    "password": "SecurePassword123!"
  }'
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "username": "johndoe",
    "created_at": 1703001234567
  },
  "message": "User registered successfully"
}
```

---

### Login
```bash
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }'
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_at": 1703087634567,
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "username": "johndoe"
    }
  }
}
```

---

### Generate API Key
```bash
curl -X POST http://localhost:8080/api/v1/auth/api-keys \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production API Key",
    "scopes": ["notifications:write", "notifications:read"],
    "expires_in_days": 90
  }'
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "key": "ns_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
    "name": "Production API Key",
    "scopes": ["notifications:write", "notifications:read"],
    "expires_at": 1710777634567,
    "created_at": 1703001234567
  },
  "message": "API key created successfully. Store this key securely - it won't be shown again."
}
```

---

## Notification Endpoints

### 1. Create Single Notification

```bash
curl -X POST http://localhost:8080/api/v1/notifications \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "message_type": "email",
    "provider": "sendgrid",
    "payload": {
      "to": "recipient@example.com",
      "subject": "Welcome to Our Service",
      "body": "Thank you for signing up!",
      "from": "noreply@example.com"
    },
    "send_at": null,
    "idempotency_key": "optional-custom-key"
  }'
```

**With Scheduled Send:**
```bash
curl -X POST http://localhost:8080/api/v1/notifications \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "message_type": "sms",
    "provider": "twilio",
    "payload": {
      "to": "+1234567890",
      "body": "Your appointment is tomorrow at 10 AM"
    },
    "send_at": 1703087634567
  }'
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "9f4b5c7d-1a2b-3c4d-5e6f-7g8h9i0j1k2l",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "message_type": "email",
    "provider": "sendgrid",
    "status": "pending",
    "idempotency_key": "sha256-hash-here",
    "created_at": 1703001234567,
    "send_at": null
  },
  "message": "Notification created and queued successfully"
}
```

**Error Response (409 Conflict - Duplicate):**
```json
{
  "success": false,
  "error": {
    "code": "DUPLICATE_NOTIFICATION",
    "message": "A similar notification was recently sent",
    "details": {
      "idempotency_key": "sha256-hash-here",
      "ttl_remaining_seconds": 3600
    }
  }
}
```

---

### 2. Create Bulk Notifications

```bash
curl -X POST http://localhost:8080/api/v1/notifications/bulk \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "notifications": [
      {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "message_type": "email",
        "provider": "sendgrid",
        "payload": {
          "to": "user1@example.com",
          "subject": "Bulk Email 1",
          "body": "Message 1"
        }
      },
      {
        "user_id": "660e8400-e29b-41d4-a716-446655440001",
        "message_type": "sms",
        "provider": "twilio",
        "payload": {
          "to": "+1234567890",
          "body": "Bulk SMS 1"
        }
      }
    ]
  }'
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "total_requested": 2,
    "created": 2,
    "failed": 0,
    "duplicates": 0,
    "notifications": [
      {
        "id": "9f4b5c7d-1a2b-3c4d-5e6f-7g8h9i0j1k2l",
        "status": "pending"
      },
      {
        "id": "8e3a4b6c-0a1b-2c3d-4e5f-6g7h8i9j0k1l",
        "status": "pending"
      }
    ]
  },
  "message": "Bulk notifications processed successfully"
}
```

---

### 3. Get Notification by ID

```bash
curl -X GET http://localhost:8080/api/v1/notifications/9f4b5c7d-1a2b-3c4d-5e6f-7g8h9i0j1k2l \
  -H "X-API-Key: your-api-key"
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "9f4b5c7d-1a2b-3c4d-5e6f-7g8h9i0j1k2l",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "message_type": "email",
    "provider": "sendgrid",
    "status": "sent",
    "payload": {
      "to": "recipient@example.com",
      "subject": "Welcome to Our Service",
      "body": "Thank you for signing up!"
    },
    "attempt_count": 1,
    "max_retries": 5,
    "created_at": 1703001234567,
    "sent_at": 1703001240123,
    "last_attempted": 1703001240123,
    "provider_response": {
      "message_id": "sendgrid-msg-id-123",
      "status": "delivered"
    }
  }
}
```

**Error Response (404 Not Found):**
```json
{
  "success": false,
  "error": {
    "code": "NOTIFICATION_NOT_FOUND",
    "message": "Notification with ID '9f4b5c7d-1a2b-3c4d-5e6f-7g8h9i0j1k2l' not found"
  }
}
```

---

### 4. List Notifications (with Pagination & Filters)

```bash
# Basic listing
curl -X GET "http://localhost:8080/api/v1/notifications?page=1&limit=20" \
  -H "X-API-Key: your-api-key"

# With filters
curl -X GET "http://localhost:8080/api/v1/notifications?page=1&limit=20&status=sent&message_type=email&user_id=550e8400-e29b-41d4-a716-446655440000" \
  -H "X-API-Key: your-api-key"

# With date range
curl -X GET "http://localhost:8080/api/v1/notifications?page=1&limit=20&created_after=1703001234567&created_before=1703087634567" \
  -H "X-API-Key: your-api-key"

# Sort by created_at descending
curl -X GET "http://localhost:8080/api/v1/notifications?page=1&limit=20&sort_by=created_at&sort_order=desc" \
  -H "X-API-Key: your-api-key"
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "notifications": [
      {
        "id": "9f4b5c7d-1a2b-3c4d-5e6f-7g8h9i0j1k2l",
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "message_type": "email",
        "provider": "sendgrid",
        "status": "sent",
        "created_at": 1703001234567,
        "sent_at": 1703001240123
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total_items": 150,
      "total_pages": 8,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

---

### 5. Cancel Scheduled Notification

```bash
curl -X DELETE http://localhost:8080/api/v1/notifications/9f4b5c7d-1a2b-3c4d-5e6f-7g8h9i0j1k2l \
  -H "X-API-Key: your-api-key"
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "9f4b5c7d-1a2b-3c4d-5e6f-7g8h9i0j1k2l",
    "status": "cancelled",
    "cancelled_at": 1703001250000
  },
  "message": "Notification cancelled successfully"
}
```

**Error Response (400 Bad Request):**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_OPERATION",
    "message": "Cannot cancel notification that has already been sent",
    "details": {
      "current_status": "sent"
    }
  }
}
```

---

### 6. Retry Failed Notification

```bash
curl -X POST http://localhost:8080/api/v1/notifications/9f4b5c7d-1a2b-3c4d-5e6f-7g8h9i0j1k2l/retry \
  -H "X-API-Key: your-api-key"
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "9f4b5c7d-1a2b-3c4d-5e6f-7g8h9i0j1k2l",
    "status": "pending",
    "attempt_count": 2,
    "scheduled_retry_at": 1703001360000
  },
  "message": "Notification queued for retry"
}
```

---

## User Endpoints

### 1. Get Current User Profile

```bash
curl -X GET http://localhost:8080/api/v1/users/me \
  -H "Authorization: Bearer your-jwt-token"
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "username": "johndoe",
    "created_at": 1703001234567,
    "updated_at": 1703001234567
  }
}
```

---

### 2. Update User Profile

```bash
curl -X PATCH http://localhost:8080/api/v1/users/me \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_updated",
    "email": "newemail@example.com"
  }'
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "newemail@example.com",
    "username": "john_updated",
    "updated_at": 1703001300000
  },
  "message": "Profile updated successfully"
}
```

---

## Template Endpoints

### 1. Create Notification Template

```bash
curl -X POST http://localhost:8080/api/v1/templates \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "welcome_email",
    "message_type": "email",
    "subject": "Welcome {{username}}!",
    "body": "Hello {{username}},\n\nWelcome to our service! Your account is ready.\n\nBest regards,\nThe Team",
    "variables": ["username"]
  }'
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "name": "welcome_email",
    "message_type": "email",
    "subject": "Welcome {{username}}!",
    "body": "Hello {{username}},\n\nWelcome to our service!...",
    "variables": ["username"],
    "is_active": true,
    "created_at": 1703001234567
  },
  "message": "Template created successfully"
}
```

---

### 2. Send Notification Using Template

```bash
curl -X POST http://localhost:8080/api/v1/notifications/from-template \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "provider": "sendgrid",
    "payload": {
      "to": "user@example.com",
      "from": "noreply@example.com"
    },
    "variables": {
      "username": "John Doe"
    }
  }'
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "9f4b5c7d-1a2b-3c4d-5e6f-7g8h9i0j1k2l",
    "template_used": "welcome_email",
    "status": "pending",
    "created_at": 1703001234567
  },
  "message": "Notification created from template"
}
```

---

### 3. List All Templates

```bash
curl -X GET "http://localhost:8080/api/v1/templates?page=1&limit=20&message_type=email" \
  -H "X-API-Key: your-api-key"
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "templates": [
      {
        "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "name": "welcome_email",
        "message_type": "email",
        "is_active": true,
        "created_at": 1703001234567
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total_items": 5,
      "total_pages": 1
    }
  }
}
```

---

### 4. Update Template

```bash
curl -X PUT http://localhost:8080/api/v1/templates/7c9e6679-7425-40de-944b-e07fc1f90ae7 \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Welcome {{username}} to our updated service!",
    "body": "Updated body text...",
    "is_active": true
  }'
```

---

### 5. Delete Template

```bash
curl -X DELETE http://localhost:8080/api/v1/templates/7c9e6679-7425-40de-944b-e07fc1f90ae7 \
  -H "X-API-Key: your-api-key"
```

---

## Webhook Endpoints

### 1. Register Webhook

```bash
curl -X POST http://localhost:8080/api/v1/webhooks \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.com/webhooks/notifications",
    "events": ["notification.sent", "notification.failed", "notification.delivered"],
    "retry_count": 3,
    "timeout_seconds": 10
  }'
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "webhook-id-123",
    "url": "https://your-app.com/webhooks/notifications",
    "secret_key": "whsec_a1b2c3d4e5f6g7h8",
    "events": ["notification.sent", "notification.failed", "notification.delivered"],
    "is_active": true,
    "created_at": 1703001234567
  },
  "message": "Webhook registered successfully. Use the secret_key to verify webhook signatures."
}
```

---

### 2. List Webhooks

```bash
curl -X GET http://localhost:8080/api/v1/webhooks \
  -H "X-API-Key: your-api-key"
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "webhooks": [
      {
        "id": "webhook-id-123",
        "url": "https://your-app.com/webhooks/notifications",
        "events": ["notification.sent", "notification.failed"],
        "is_active": true,
        "created_at": 1703001234567
      }
    ]
  }
}
```

---

### 3. Test Webhook

```bash
curl -X POST http://localhost:8080/api/v1/webhooks/webhook-id-123/test \
  -H "X-API-Key: your-api-key"
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "delivered": true,
    "response_status": 200,
    "response_time_ms": 145
  },
  "message": "Webhook test successful"
}
```

---

### 4. Webhook Payload Example

When a notification event occurs, the system sends a POST request to your webhook URL:

```bash
# This is what your server receives
POST https://your-app.com/webhooks/notifications
Headers:
  Content-Type: application/json
  X-Webhook-Signature: sha256=abcd1234...
  X-Webhook-ID: webhook-id-123
  X-Event-Type: notification.sent

Body:
{
  "event": "notification.sent",
  "timestamp": 1703001234567,
  "notification": {
    "id": "9f4b5c7d-1a2b-3c4d-5e6f-7g8h9i0j1k2l",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "message_type": "email",
    "provider": "sendgrid",
    "status": "sent",
    "sent_at": 1703001234567
  }
}
```

**Verify Signature (Example in Go):**
```go
import (
    "crypto/hmac"
    "crypto/sha256"
    "encoding/hex"
)

func verifyWebhookSignature(payload []byte, signature, secret string) bool {
    h := hmac.New(sha256.New, []byte(secret))
    h.Write(payload)
    expected := "sha256=" + hex.EncodeToString(h.Sum(nil))
    return hmac.Equal([]byte(expected), []byte(signature))
}
```

---

### 5. Delete Webhook

```bash
curl -X DELETE http://localhost:8080/api/v1/webhooks/webhook-id-123 \
  -H "X-API-Key: your-api-key"
```

---

## Preference Endpoints

### 1. Get User Notification Preferences

```bash
curl -X GET http://localhost:8080/api/v1/preferences \
  -H "Authorization: Bearer your-jwt-token"
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "preferences": [
      {
        "channel": "email",
        "enabled": true,
        "frequency_cap": 50,
        "quiet_hours_start": "22:00",
        "quiet_hours_end": "08:00",
        "timezone": "America/New_York"
      },
      {
        "channel": "sms",
        "enabled": true,
        "frequency_cap": 10,
        "quiet_hours_start": null,
        "quiet_hours_end": null,
        "timezone": "America/New_York"
      }
    ]
  }
}
```

---

### 2. Update Notification Preferences

```bash
curl -X PUT http://localhost:8080/api/v1/preferences \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "email",
    "enabled": true,
    "frequency_cap": 30,
    "quiet_hours_start": "23:00",
    "quiet_hours_end": "07:00",
    "timezone": "America/Los_Angeles"
  }'
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "channel": "email",
    "enabled": true,
    "frequency_cap": 30,
    "quiet_hours_start": "23:00",
    "quiet_hours_end": "07:00",
    "timezone": "America/Los_Angeles",
    "updated_at": 1703001300000
  },
  "message": "Preferences updated successfully"
}
```

---

## Analytics Endpoints

### 1. Get Notification Statistics

```bash
curl -X GET "http://localhost:8080/api/v1/analytics/stats?start_date=2024-01-01&end_date=2024-01-31&group_by=day" \
  -H "X-API-Key: your-api-key"
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "period": {
      "start": "2024-01-01",
      "end": "2024-01-31"
    },
    "summary": {
      "total_sent": 15420,
      "total_failed": 342,
      "total_pending": 128,
      "success_rate": 97.8,
      "avg_delivery_time_ms": 2340
    },
    "by_type": {
      "email": {
        "sent": 10200,
        "failed": 180,
        "success_rate": 98.3
      },
      "sms": {
        "sent": 3820,
        "failed": 102,
        "success_rate": 97.4
      },
      "push": {
        "sent": 1400,
        "failed": 60,
        "success_rate": 95.9
      }
    },
    "by_provider": {
      "sendgrid": {
        "sent": 10200,
        "failed": 180,
        "avg_delivery_time_ms": 2100
      },
      "twilio": {
        "sent": 3820,
        "failed": 102,
        "avg_delivery_time_ms": 2800
      }
    },
    "timeline": [
      {
        "date": "2024-01-01",
        "sent": 500,
        "failed": 12
      }
    ]
  }
}
```

---

### 2. Export Analytics Report

```bash
curl -X GET "http://localhost:8080/api/v1/analytics/export?format=csv&start_date=2024-01-01&end_date=2024-01-31" \
  -H "X-API-Key: your-api-key" \
  -o report.csv
```

---

## DLQ Management Endpoints

### 1. List DLQ Entries

```bash
curl -X GET "http://localhost:8080/api/v1/dlq?page=1&limit=20&resolved=false" \
  -H "X-API-Key: your-api-key"
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "entries": [
      {
        "id": "dlq-entry-id-123",
        "notification_id": "9f4b5c7d-1a2b-3c4d-5e6f-7g8h9i0j1k2l",
        "failure_reason": "provider_rate_limit_exceeded",
        "retry_history": [
          {
            "attempt": 1,
            "timestamp": 1703001234567,
            "error": "Rate limit exceeded"
          }
        ],
        "moved_to_dlq_at": 1703001500000,
        "resolved": false
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total_items": 45,
      "total_pages": 3
    }
  }
}
```

---

### 2. Retry DLQ Entry

```bash
curl -X POST http://localhost:8080/api/v1/dlq/dlq-entry-id-123/retry \
  -H "X-API-Key: your-api-key"
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "dlq-entry-id-123",
    "notification_id": "9f4b5c7d-1a2b-3c4d-5e6f-7g8h9i0j1k2l",
    "status": "requeued"
  },
  "message": "Notification moved from DLQ to retry queue"
}
```

---

### 3. Resolve DLQ Entry

```bash
curl -X POST http://localhost:8080/api/v1/dlq/dlq-entry-id-123/resolve \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "resolution_note": "Fixed provider configuration issue"
  }'
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "dlq-entry-id-123",
    "resolved": true,
    "resolved_at": 1703001600000,
    "resolved_by": "550e8400-e29b-41d4-a716-446655440000"
  },
  "message": "DLQ entry marked as resolved"
}
```

---

## Health Check Endpoints

### 1. Basic Health Check

```bash
curl -X GET http://localhost:8080/health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": 1703001234567,
  "uptime_seconds": 86400
}
```

---

### 2. Detailed Readiness Check

```bash
curl -X GET http://localhost:8080/ready
```

**Response (200 OK):**
```json
{
  "status": "ready",
  "timestamp": 1703001234567,
  "checks": {
    "database": {
      "status": "healthy",
      "latency_ms": 12
    },
    "redis": {
      "status": "healthy",
      "latency_ms": 3
    },
    "queue": {
      "status": "healthy",
      "depth": 245
    },
    "providers": {
      "sendgrid": "healthy",
      "twilio": "healthy",
      "fcm": "degraded"
    }
  }
}
```

---

## Error Response Format

All error responses follow this standard format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "Additional context"
    }
  }
}
```

### Common Error Codes

| HTTP Status | Error Code                  | Description                          |
|-------------|-----------------------------|--------------------------------------|
| 400         | INVALID_REQUEST             | Request validation failed            |
| 401         | UNAUTHORIZED                | Authentication required              |
| 403         | FORBIDDEN                   | Insufficient permissions             |
| 404         | NOT_FOUND                   | Resource not found                   |
| 409         | DUPLICATE_NOTIFICATION      | Duplicate notification detected      |
| 429         | RATE_LIMIT_EXCEEDED         | Too many requests                    |
| 500         | INTERNAL_SERVER_ERROR       | Server error                         |
| 503         | SERVICE_UNAVAILABLE         | Service temporarily unavailable      |

---

## Rate Limits

Default rate limits per API key:

- **Standard tier**: 100 requests/minute, 10,000 requests/day
- **Premium tier**: 1,000 requests/minute, 100,000 requests/day

Rate limit headers included in all responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1703001294
```

---

## Pagination

All list endpoints support pagination with these query parameters:

- `page` (default: 1)
- `limit` (default: 20, max: 100)
- `sort_by` (field name)
- `sort_order` (asc/desc)

---

## Filtering

Common filter parameters across endpoints:

- `status` - Filter by notification status
- `message_type` - Filter by type (email, sms, push)
- `provider` - Filter by provider
- `created_after` - Timestamp in milliseconds
- `created_before` - Timestamp in milliseconds
- `user_id` - Filter by user

---

## Best Practices

1. **Always use HTTPS** in production
2. **Store API keys securely** - Never commit to version control
3. **Implement exponential backoff** for retries
4. **Verify webhook signatures** to ensure authenticity
5. **Use idempotency keys** for critical operations
6. **Monitor rate limits** to avoid throttling
7. **Handle errors gracefully** with proper retry logic
8. **Use bulk endpoints** for batch operations

---

## Testing with Postman

Import the API collection:
```bash
curl -o notification-api.postman_collection.json \
  http://localhost:8080/api/v1/postman-collection
```

---

## Support

For API support:
- Email: api-support@example.com
- Docs: https://docs.example.com
- Status: https://status.example.com
