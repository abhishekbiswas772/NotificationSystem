# Database Schema - Notification System

## Overview
This document outlines the complete database structure for a production-level notification system.

---

## Tables

### 1. **users**
Stores user information.

| Column        | Type         | Constraints                    | Description                          |
|---------------|--------------|--------------------------------|--------------------------------------|
| id            | CHAR(36)     | PRIMARY KEY                    | UUID for user                        |
| email         | VARCHAR(255) | UNIQUE, NOT NULL               | User email address                   |
| username      | VARCHAR(100) | UNIQUE, NOT NULL               | Username                             |
| created_at    | BIGINT       | NOT NULL, AUTO                 | Creation timestamp (milliseconds)    |
| updated_at    | BIGINT       | NOT NULL, AUTO                 | Last update timestamp (milliseconds) |

**Indexes:**
- `idx_users_email` on `email`
- `idx_users_username` on `username`

---

### 2. **notifications**
Main table for storing all notifications.

| Column             | Type         | Constraints                           | Description                                    |
|--------------------|--------------|---------------------------------------|------------------------------------------------|
| id                 | CHAR(36)     | PRIMARY KEY                           | UUID for notification                          |
| user_id            | CHAR(36)     | NOT NULL, FOREIGN KEY → users(id)     | Reference to user                              |
| idempotency_key    | VARCHAR(64)  | UNIQUE, NOT NULL                      | SHA-256 hash for deduplication                 |
| message_type       | VARCHAR(20)  | NOT NULL                              | Type: 'sms', 'email', 'push'                   |
| provider           | VARCHAR(20)  | NOT NULL                              | Provider: 'sendgrid', 'twilio', 'fcm'          |
| status             | VARCHAR(20)  | NOT NULL, DEFAULT 'pending'           | Status: pending, sent, failed, cancelled       |
| payload            | TEXT         | NOT NULL                              | JSON payload with message content              |
| attempt_count      | INT          | NOT NULL, DEFAULT 0                   | Number of send attempts                        |
| max_retries        | INT          | NOT NULL, DEFAULT 5                   | Maximum retry attempts                         |
| created_at         | BIGINT       | NOT NULL, AUTO                        | Creation timestamp (milliseconds)              |
| last_attempted     | BIGINT       | NULL                                  | Last attempt timestamp                         |
| send_at            | BIGINT       | NULL                                  | Scheduled send time (for delayed notifications)|
| failed_at          | BIGINT       | NULL                                  | Failure timestamp                              |
| sent_at            | BIGINT       | NULL                                  | Successful send timestamp                      |
| error_message      | TEXT         | NULL                                  | Error details if failed                        |
| provider_response  | TEXT         | NULL                                  | Response from provider                         |

**Indexes:**
- `idx_user_type` on `(user_id, message_type)` - Composite index
- `idx_user_status` on `(user_id, status)` - Composite index
- `idx_status_created` on `(status, created_at)` - Composite index
- `idx_idempotency` on `idempotency_key` - Unique index
- `idx_send_at` on `send_at` - For scheduled notifications

**Foreign Keys:**
- `user_id` → `users(id)` ON UPDATE CASCADE ON DELETE CASCADE

---

### 3. **notification_dlq**
Dead Letter Queue for failed notifications that exceeded retry limits.

| Column           | Type         | Constraints                                  | Description                                |
|------------------|--------------|----------------------------------------------|--------------------------------------------|
| id               | CHAR(36)     | PRIMARY KEY                                  | UUID for DLQ entry                         |
| notification_id  | CHAR(36)     | UNIQUE, NOT NULL, FOREIGN KEY → notifications(id) | Reference to failed notification           |
| failure_reason   | TEXT         | NOT NULL                                     | Categorized failure reason                 |
| retry_history    | TEXT         | NULL                                         | JSON array of retry attempts with details  |
| moved_to_dlq_at  | BIGINT       | NOT NULL, AUTO                               | Timestamp when moved to DLQ                |
| resolved         | BOOLEAN      | NOT NULL, DEFAULT false                      | Whether issue has been resolved            |
| resolved_at      | BIGINT       | NULL                                         | Resolution timestamp                       |
| resolved_by      | CHAR(36)     | NULL, FOREIGN KEY → users(id)                | User who resolved the issue                |

**Indexes:**
- `idx_notification_dlq` on `notification_id` - Unique index
- `idx_moved_at` on `moved_to_dlq_at`
- `idx_resolved` on `resolved`

**Foreign Keys:**
- `notification_id` → `notifications(id)` ON UPDATE CASCADE ON DELETE CASCADE
- `resolved_by` → `users(id)` ON UPDATE CASCADE ON DELETE SET NULL

---

### 4. **notification_templates**
Store reusable notification templates.

| Column          | Type         | Constraints                    | Description                              |
|-----------------|--------------|--------------------------------|------------------------------------------|
| id              | CHAR(36)     | PRIMARY KEY                    | UUID for template                        |
| name            | VARCHAR(100) | UNIQUE, NOT NULL               | Template name/identifier                 |
| message_type    | VARCHAR(20)  | NOT NULL                       | Type: 'sms', 'email', 'push'             |
| subject         | VARCHAR(255) | NULL                           | Email subject (null for SMS/push)        |
| body            | TEXT         | NOT NULL                       | Template body with placeholders          |
| variables       | TEXT         | NULL                           | JSON array of variable names             |
| is_active       | BOOLEAN      | NOT NULL, DEFAULT true         | Whether template is active               |
| created_by      | CHAR(36)     | NOT NULL, FOREIGN KEY → users(id) | User who created template                |
| created_at      | BIGINT       | NOT NULL, AUTO                 | Creation timestamp                       |
| updated_at      | BIGINT       | NOT NULL, AUTO                 | Last update timestamp                    |

**Indexes:**
- `idx_template_name` on `name`
- `idx_template_type` on `message_type`
- `idx_template_active` on `is_active`

**Foreign Keys:**
- `created_by` → `users(id)` ON UPDATE CASCADE ON DELETE SET NULL

---

### 5. **notification_webhooks**
Store webhook configurations for notification status callbacks.

| Column           | Type         | Constraints                           | Description                              |
|------------------|--------------|---------------------------------------|------------------------------------------|
| id               | CHAR(36)     | PRIMARY KEY                           | UUID for webhook                         |
| user_id          | CHAR(36)     | NOT NULL, FOREIGN KEY → users(id)     | User who owns webhook                    |
| url              | VARCHAR(500) | NOT NULL                              | Webhook callback URL                     |
| secret_key       | VARCHAR(64)  | NOT NULL                              | HMAC secret for signature verification   |
| events           | TEXT         | NOT NULL                              | JSON array of events to subscribe to     |
| is_active        | BOOLEAN      | NOT NULL, DEFAULT true                | Whether webhook is active                |
| retry_count      | INT          | NOT NULL, DEFAULT 3                   | Number of retries for failed webhooks    |
| timeout_seconds  | INT          | NOT NULL, DEFAULT 10                  | Webhook request timeout                  |
| created_at       | BIGINT       | NOT NULL, AUTO                        | Creation timestamp                       |
| updated_at       | BIGINT       | NOT NULL, AUTO                        | Last update timestamp                    |

**Indexes:**
- `idx_webhook_user` on `user_id`
- `idx_webhook_active` on `is_active`

**Foreign Keys:**
- `user_id` → `users(id)` ON UPDATE CASCADE ON DELETE CASCADE

---

### 6. **webhook_deliveries**
Track webhook delivery attempts and status.

| Column           | Type         | Constraints                                | Description                           |
|------------------|--------------|--------------------------------------------|---------------------------------------|
| id               | CHAR(36)     | PRIMARY KEY                                | UUID for delivery attempt             |
| webhook_id       | CHAR(36)     | NOT NULL, FOREIGN KEY → notification_webhooks(id) | Reference to webhook                  |
| notification_id  | CHAR(36)     | NOT NULL, FOREIGN KEY → notifications(id)  | Reference to notification             |
| event_type       | VARCHAR(50)  | NOT NULL                                   | Event: sent, failed, delivered, etc.  |
| payload          | TEXT         | NOT NULL                                   | JSON payload sent to webhook          |
| response_status  | INT          | NULL                                       | HTTP response status code             |
| response_body    | TEXT         | NULL                                       | Response body from webhook            |
| attempt_count    | INT          | NOT NULL, DEFAULT 1                        | Delivery attempt number               |
| delivered        | BOOLEAN      | NOT NULL, DEFAULT false                    | Whether delivery was successful       |
| delivered_at     | BIGINT       | NULL                                       | Successful delivery timestamp         |
| created_at       | BIGINT       | NOT NULL, AUTO                             | Creation timestamp                    |
| next_retry_at    | BIGINT       | NULL                                       | Next retry scheduled time             |

**Indexes:**
- `idx_webhook_delivery` on `(webhook_id, notification_id)` - Composite index
- `idx_delivery_status` on `delivered`
- `idx_next_retry` on `next_retry_at`

**Foreign Keys:**
- `webhook_id` → `notification_webhooks(id)` ON UPDATE CASCADE ON DELETE CASCADE
- `notification_id` → `notifications(id)` ON UPDATE CASCADE ON DELETE CASCADE

---

### 7. **notification_preferences**
User preferences for notification delivery.

| Column              | Type         | Constraints                           | Description                              |
|---------------------|--------------|---------------------------------------|------------------------------------------|
| id                  | CHAR(36)     | PRIMARY KEY                           | UUID for preference                      |
| user_id             | CHAR(36)     | NOT NULL, FOREIGN KEY → users(id)     | User who owns preference                 |
| channel             | VARCHAR(20)  | NOT NULL                              | Channel: 'sms', 'email', 'push'          |
| enabled             | BOOLEAN      | NOT NULL, DEFAULT true                | Whether channel is enabled               |
| frequency_cap       | INT          | NULL                                  | Max notifications per day (null = unlimited) |
| quiet_hours_start   | TIME         | NULL                                  | Start of quiet hours (local time)        |
| quiet_hours_end     | TIME         | NULL                                  | End of quiet hours (local time)          |
| timezone            | VARCHAR(50)  | NOT NULL, DEFAULT 'UTC'               | User timezone                            |
| created_at          | BIGINT       | NOT NULL, AUTO                        | Creation timestamp                       |
| updated_at          | BIGINT       | NOT NULL, AUTO                        | Last update timestamp                    |

**Indexes:**
- `idx_user_channel` on `(user_id, channel)` - Composite unique index
- `idx_preference_enabled` on `enabled`

**Foreign Keys:**
- `user_id` → `users(id)` ON UPDATE CASCADE ON DELETE CASCADE

---

### 8. **provider_configs**
Store provider-specific configurations.

| Column           | Type         | Constraints                    | Description                              |
|------------------|--------------|--------------------------------|------------------------------------------|
| id               | CHAR(36)     | PRIMARY KEY                    | UUID for config                          |
| provider_name    | VARCHAR(50)  | UNIQUE, NOT NULL               | Provider: 'sendgrid', 'twilio', 'fcm'    |
| api_key          | VARCHAR(255) | NOT NULL                       | Encrypted API key                        |
| api_secret       | VARCHAR(255) | NULL                           | Encrypted API secret (if needed)         |
| config_json      | TEXT         | NULL                           | Additional JSON configuration            |
| is_active        | BOOLEAN      | NOT NULL, DEFAULT true         | Whether provider is active               |
| rate_limit       | INT          | NULL                           | Rate limit (requests per minute)         |
| timeout_seconds  | INT          | NOT NULL, DEFAULT 30           | Provider request timeout                 |
| priority         | INT          | NOT NULL, DEFAULT 0            | Priority (higher = preferred)            |
| created_at       | BIGINT       | NOT NULL, AUTO                 | Creation timestamp                       |
| updated_at       | BIGINT       | NOT NULL, AUTO                 | Last update timestamp                    |

**Indexes:**
- `idx_provider_name` on `provider_name`
- `idx_provider_active` on `is_active`
- `idx_provider_priority` on `priority`

---

### 9. **notification_metrics**
Aggregated metrics for analytics.

| Column           | Type         | Constraints                    | Description                              |
|------------------|--------------|--------------------------------|------------------------------------------|
| id               | CHAR(36)     | PRIMARY KEY                    | UUID for metric                          |
| date             | DATE         | NOT NULL                       | Metric date                              |
| hour             | INT          | NULL                           | Hour (0-23) for hourly metrics           |
| provider         | VARCHAR(20)  | NOT NULL                       | Provider name                            |
| message_type     | VARCHAR(20)  | NOT NULL                       | Message type                             |
| total_sent       | INT          | NOT NULL, DEFAULT 0            | Total notifications sent                 |
| total_failed     | INT          | NOT NULL, DEFAULT 0            | Total notifications failed               |
| total_pending    | INT          | NOT NULL, DEFAULT 0            | Total notifications pending              |
| avg_delivery_ms  | BIGINT       | NULL                           | Average delivery time (milliseconds)     |
| created_at       | BIGINT       | NOT NULL, AUTO                 | Creation timestamp                       |

**Indexes:**
- `idx_metrics_date` on `(date, hour)` - Composite index
- `idx_metrics_provider` on `provider`
- `idx_metrics_type` on `message_type`

---

### 10. **api_keys**
Store API keys for authentication.

| Column           | Type         | Constraints                           | Description                              |
|------------------|--------------|---------------------------------------|------------------------------------------|
| id               | CHAR(36)     | PRIMARY KEY                           | UUID for API key                         |
| user_id          | CHAR(36)     | NOT NULL, FOREIGN KEY → users(id)     | User who owns API key                    |
| key_hash         | VARCHAR(64)  | UNIQUE, NOT NULL                      | SHA-256 hash of API key                  |
| name             | VARCHAR(100) | NOT NULL                              | Friendly name for key                    |
| scopes           | TEXT         | NULL                                  | JSON array of permissions                |
| is_active        | BOOLEAN      | NOT NULL, DEFAULT true                | Whether key is active                    |
| expires_at       | BIGINT       | NULL                                  | Expiration timestamp (null = never)      |
| last_used_at     | BIGINT       | NULL                                  | Last usage timestamp                     |
| created_at       | BIGINT       | NOT NULL, AUTO                        | Creation timestamp                       |

**Indexes:**
- `idx_api_key_hash` on `key_hash`
- `idx_api_key_user` on `user_id`
- `idx_api_key_active` on `is_active`

**Foreign Keys:**
- `user_id` → `users(id)` ON UPDATE CASCADE ON DELETE CASCADE

---

### 11. **rate_limits**
Track rate limit usage per user.

| Column           | Type         | Constraints                           | Description                              |
|------------------|--------------|---------------------------------------|------------------------------------------|
| id               | CHAR(36)     | PRIMARY KEY                           | UUID for rate limit entry                |
| user_id          | CHAR(36)     | NOT NULL, FOREIGN KEY → users(id)     | User reference                           |
| window_start     | BIGINT       | NOT NULL                              | Rate limit window start time             |
| request_count    | INT          | NOT NULL, DEFAULT 0                   | Number of requests in window             |
| limit_type       | VARCHAR(20)  | NOT NULL                              | Type: 'api', 'notification'              |
| created_at       | BIGINT       | NOT NULL, AUTO                        | Creation timestamp                       |
| updated_at       | BIGINT       | NOT NULL, AUTO                        | Last update timestamp                    |

**Indexes:**
- `idx_rate_limit_user_window` on `(user_id, window_start, limit_type)` - Composite unique index

**Foreign Keys:**
- `user_id` → `users(id)` ON UPDATE CASCADE ON DELETE CASCADE

---

### 12. **audit_logs**
Track all important system events for compliance.

| Column           | Type         | Constraints                           | Description                              |
|------------------|--------------|---------------------------------------|------------------------------------------|
| id               | CHAR(36)     | PRIMARY KEY                           | UUID for log entry                       |
| user_id          | CHAR(36)     | NULL, FOREIGN KEY → users(id)         | User who performed action                |
| action           | VARCHAR(100) | NOT NULL                              | Action: create, update, delete, etc.     |
| resource_type    | VARCHAR(50)  | NOT NULL                              | Resource: notification, user, webhook    |
| resource_id      | CHAR(36)     | NULL                                  | ID of affected resource                  |
| ip_address       | VARCHAR(45)  | NULL                                  | IP address (IPv4 or IPv6)                |
| user_agent       | TEXT         | NULL                                  | HTTP User-Agent header                   |
| changes          | TEXT         | NULL                                  | JSON of old/new values                   |
| created_at       | BIGINT       | NOT NULL, AUTO                        | Creation timestamp                       |

**Indexes:**
- `idx_audit_user` on `user_id`
- `idx_audit_action` on `action`
- `idx_audit_resource` on `(resource_type, resource_id)` - Composite index
- `idx_audit_created` on `created_at`

**Foreign Keys:**
- `user_id` → `users(id)` ON UPDATE CASCADE ON DELETE SET NULL

---

## Relationships Diagram (Text-based)

```
users
  |
  |-- 1:N --> notifications
  |-- 1:N --> notification_preferences
  |-- 1:N --> notification_webhooks
  |-- 1:N --> api_keys
  |-- 1:N --> rate_limits
  |-- 1:N --> audit_logs
  |-- 1:N --> notification_templates (created_by)

notifications
  |
  |-- 1:1 --> notification_dlq
  |-- 1:N --> webhook_deliveries

notification_webhooks
  |
  |-- 1:N --> webhook_deliveries

notification_dlq
  |
  |-- N:1 --> users (resolved_by)
```

---

## Data Types & Constraints Summary

### Primary Keys
All tables use `CHAR(36)` UUIDs as primary keys for:
- Global uniqueness
- No sequence conflicts in distributed systems
- Non-sequential for security

### Timestamps
All timestamps use `BIGINT` storing milliseconds since epoch:
- Consistent precision across platforms
- Easy to work with in Go (time.UnixMilli())
- Supports far future dates

### Text Fields
- Short identifiers: `VARCHAR(20-100)`
- Long text/JSON: `TEXT`
- URLs: `VARCHAR(500)`

---

## Indexes Strategy

1. **Composite Indexes**: Used for common query patterns (user_id + status, user_id + type)
2. **Unique Indexes**: Enforce data integrity (email, idempotency_key)
3. **Foreign Key Indexes**: Improve JOIN performance
4. **Timestamp Indexes**: Support time-range queries and sorting

---

## Migration Strategy

### Initial Migration
Create all tables with proper constraints and indexes.

### Future Migrations
- Use `golang-migrate` for version control
- Always include rollback scripts
- Test migrations on staging first
- Use online DDL for large tables (avoid locking)

---

## Performance Considerations

1. **Partitioning**: Consider partitioning `notifications` table by `created_at` (monthly partitions)
2. **Archiving**: Archive old notifications (>90 days) to separate cold storage table
3. **Indexes**: Monitor slow queries and add indexes as needed
4. **Vacuuming**: Regular VACUUM on PostgreSQL for performance
5. **Connection Pooling**: Use pgBouncer or similar for connection management

---

## Security Considerations

1. **Encryption at Rest**: Enable database encryption
2. **Sensitive Data**: Encrypt `api_key`, `api_secret`, `secret_key` fields
3. **Access Control**: Use least-privilege database users
4. **SQL Injection**: Always use parameterized queries (GORM does this)
5. **PII Handling**: Hash or encrypt user emails if required by compliance

---

## Backup Strategy

1. **Full Backups**: Daily full database backups
2. **WAL Archiving**: Continuous WAL archiving for point-in-time recovery
3. **Retention**: Keep 30 days of backups
4. **Testing**: Regular backup restoration tests

---

## Monitoring Queries

### Check notification status distribution
```sql
SELECT status, COUNT(*)
FROM notifications
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY status;
```

### Find slow/stuck notifications
```sql
SELECT id, user_id, status, attempt_count, created_at
FROM notifications
WHERE status = 'pending'
  AND created_at < NOW() - INTERVAL '1 hour';
```

### DLQ size check
```sql
SELECT COUNT(*) FROM notification_dlq WHERE resolved = false;
```

### Provider performance
```sql
SELECT provider,
       COUNT(*) as total,
       SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent,
       SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
FROM notifications
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY provider;
```

---

## Notes

- All foreign keys use `CASCADE` for updates and appropriate actions for deletes
- All tables have `created_at` timestamps for audit trails
- Boolean fields default to `false` for safety
- Use transactions for multi-table operations
- Consider adding `deleted_at` for soft deletes if needed
