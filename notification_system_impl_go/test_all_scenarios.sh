#!/bin/bash

# Test all notification scenarios for Go implementation
# Tests 10 different scenarios with local providers

API_BASE="http://localhost:8080/api/v1"
USER_ID="test-user-go-123"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_test() {
    echo -e "\n${BLUE}======================================================================${NC}"
    echo -e "${YELLOW}Test $1/10: $2${NC}"
    echo -e "${BLUE}======================================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Test 1: Email via Local Provider
test_1() {
    print_test 1 "Email via Local Provider"

    curl -X POST "${API_BASE}/notifications" \
        -H "Content-Type: application/json" \
        -d '{
            "user_id": "'"$USER_ID"'",
            "message_type": "email",
            "provider": "local",
            "payload": "{\"to\":\"user@example.com\",\"subject\":\"Test Email\",\"body\":\"<h1>Hello from Go Notification System!</h1>\"}",
            "idempotency_key": "test-1-'$(date +%s)'"
        }' -s | jq '.'

    sleep 2
}

# Test 2: SMS via Console Provider
test_2() {
    print_test 2 "SMS via Console Provider"

    curl -X POST "${API_BASE}/notifications" \
        -H "Content-Type: application/json" \
        -d '{
            "user_id": "'"$USER_ID"'",
            "message_type": "sms",
            "provider": "console_sms",
            "payload": "{\"to\":\"+1234567890\",\"body\":\"Hello! This is a test SMS from Go Notification System.\"}",
            "idempotency_key": "test-2-'$(date +%s)'"
        }' -s | jq '.'

    sleep 2
}

# Test 3: Push via Local Provider
test_3() {
    print_test 3 "Push Notification via Local Provider"

    curl -X POST "${API_BASE}/notifications" \
        -H "Content-Type: application/json" \
        -d '{
            "user_id": "'"$USER_ID"'",
            "message_type": "push",
            "provider": "local",
            "payload": "{\"token\":\"device-token-123\",\"title\":\"New Message\",\"body\":\"You have a new notification!\",\"data\":{\"order_id\":\"12345\"}}",
            "idempotency_key": "test-3-'$(date +%s)'"
        }' -s | jq '.'

    sleep 2
}

# Test 4: Bulk Create
test_4() {
    print_test 4 "Bulk Create (3 notifications)"

    curl -X POST "${API_BASE}/notifications/bulk" \
        -H "Content-Type: application/json" \
        -d '[
            {
                "user_id": "'"$USER_ID"'",
                "message_type": "email",
                "provider": "local",
                "payload": "{\"to\":\"user1@example.com\",\"subject\":\"Bulk 1\",\"body\":\"Message 1\"}",
                "idempotency_key": "bulk-1-'$(date +%s)'"
            },
            {
                "user_id": "'"$USER_ID"'",
                "message_type": "sms",
                "provider": "console_sms",
                "payload": "{\"to\":\"+1111111111\",\"body\":\"Bulk SMS 2\"}",
                "idempotency_key": "bulk-2-'$(date +%s)'"
            },
            {
                "user_id": "'"$USER_ID"'",
                "message_type": "push",
                "provider": "local",
                "payload": "{\"token\":\"token-3\",\"title\":\"Bulk 3\",\"body\":\"Message 3\"}",
                "idempotency_key": "bulk-3-'$(date +%s)'"
            }
        ]' -s | jq '.'

    sleep 3
}

# Test 5: Scheduled Notification
test_5() {
    print_test 5 "Scheduled Notification (10 seconds from now)"

    FUTURE_TIME=$(($(date +%s) + 10))000  # 10 seconds from now in milliseconds

    curl -X POST "${API_BASE}/notifications" \
        -H "Content-Type: application/json" \
        -d '{
            "user_id": "'"$USER_ID"'",
            "message_type": "email",
            "provider": "local",
            "payload": "{\"to\":\"scheduled@example.com\",\"subject\":\"Scheduled\",\"body\":\"This was scheduled!\"}",
            "send_at": '"$FUTURE_TIME"',
            "idempotency_key": "test-5-'$(date +%s)'"
        }' -s | jq '.'

    print_success "Scheduled for $(date -r $((FUTURE_TIME/1000)))"
    sleep 1
}

# Test 6: Idempotency
test_6() {
    print_test 6 "Idempotency (send same notification twice)"

    IDEMP_KEY="duplicate-test-$(date +%s)"

    echo "  Attempt 1:"
    RESP1=$(curl -X POST "${API_BASE}/notifications" \
        -H "Content-Type: application/json" \
        -d '{
            "user_id": "'"$USER_ID"'",
            "message_type": "email",
            "provider": "local",
            "payload": "{\"to\":\"duplicate@example.com\",\"subject\":\"Duplicate\",\"body\":\"Test\"}",
            "idempotency_key": "'"$IDEMP_KEY"'"
        }' -s)
    echo "$RESP1" | jq '.'

    sleep 1

    echo -e "\n  Attempt 2 (should fail):"
    RESP2=$(curl -X POST "${API_BASE}/notifications" \
        -H "Content-Type: application/json" \
        -d '{
            "user_id": "'"$USER_ID"'",
            "message_type": "email",
            "provider": "local",
            "payload": "{\"to\":\"duplicate@example.com\",\"subject\":\"Duplicate\",\"body\":\"Test\"}",
            "idempotency_key": "'"$IDEMP_KEY"'"
        }' -s)
    echo "$RESP2" | jq '.'

    print_success "Idempotency test completed"
    sleep 1
}

# Test 7: List Notifications
test_7() {
    print_test 7 "List User Notifications"

    curl -X GET "${API_BASE}/notifications?user_id=${USER_ID}&limit=10" \
        -H "Content-Type: application/json" \
        -s | jq '.'

    sleep 1
}

# Test 8: Cancel Notification
test_8() {
    print_test 8 "Cancel Notification"

    # Create notification
    FUTURE_TIME=$(($(date +%s) + 60))000
    NOTIF=$(curl -X POST "${API_BASE}/notifications" \
        -H "Content-Type: application/json" \
        -d '{
            "user_id": "'"$USER_ID"'",
            "message_type": "email",
            "provider": "local",
            "payload": "{\"to\":\"cancel@example.com\",\"subject\":\"To Cancel\",\"body\":\"This will be cancelled\"}",
            "send_at": '"$FUTURE_TIME"',
            "idempotency_key": "cancel-test-'$(date +%s)'"
        }' -s)

    NOTIF_ID=$(echo "$NOTIF" | jq -r '.id // .data.id // empty')

    if [ -n "$NOTIF_ID" ]; then
        print_success "Created notification: $NOTIF_ID"
        sleep 1

        # Cancel it
        echo "  Cancelling..."
        curl -X DELETE "${API_BASE}/notifications/${NOTIF_ID}" \
            -H "Content-Type: application/json" \
            -s | jq '.'

        print_success "Notification cancelled"
    else
        print_error "Failed to create notification"
    fi

    sleep 1
}

# Test 9: Get Single Notification
test_9() {
    print_test 9 "Get Single Notification"

    # Create notification
    NOTIF=$(curl -X POST "${API_BASE}/notifications" \
        -H "Content-Type: application/json" \
        -d '{
            "user_id": "'"$USER_ID"'",
            "message_type": "sms",
            "provider": "console_sms",
            "payload": "{\"to\":\"+9999999999\",\"body\":\"Get test\"}",
            "idempotency_key": "get-test-'$(date +%s)'"
        }' -s)

    NOTIF_ID=$(echo "$NOTIF" | jq -r '.id // .data.id // empty')

    if [ -n "$NOTIF_ID" ]; then
        print_success "Created notification: $NOTIF_ID"
        sleep 2

        # Get it
        echo "  Retrieving..."
        curl -X GET "${API_BASE}/notifications/${NOTIF_ID}" \
            -H "Content-Type: application/json" \
            -s | jq '.'
    else
        print_error "Failed to create notification"
    fi

    sleep 1
}

# Test 10: Queue Processing
test_10() {
    print_test 10 "Queue Processing (5 notifications)"

    for i in {1..5}; do
        if [ $((i % 2)) -eq 0 ]; then
            TYPE="email"
            PROVIDER="local"
            PAYLOAD="{\"to\":\"retry${i}@example.com\",\"subject\":\"Queue Test ${i}\",\"body\":\"Testing queue - Message ${i}\"}"
        else
            TYPE="sms"
            PROVIDER="console_sms"
            PAYLOAD="{\"to\":\"+${i}111\",\"body\":\"Testing queue - Message ${i}\"}"
        fi

        curl -X POST "${API_BASE}/notifications" \
            -H "Content-Type: application/json" \
            -d '{
                "user_id": "'"$USER_ID"'",
                "message_type": "'"$TYPE"'",
                "provider": "'"$PROVIDER"'",
                "payload": "'"$PAYLOAD"'",
                "max_retries": 3,
                "idempotency_key": "queue-test-'"$i"'-'$(date +%s)'"
            }' -s > /dev/null

        echo "  Created notification $i/5"
        sleep 0.5
    done

    print_success "Created 5 notifications - check worker logs for processing"
}

# Main execution
main() {
    echo -e "\n${BLUE}======================================================================${NC}"
    echo -e "${YELLOW}Go Notification System - Comprehensive Test Suite${NC}"
    echo -e "${BLUE}======================================================================${NC}"
    echo -e "\nAPI Base: ${API_BASE}"

    # Create test user first (or get existing user)
    echo -e "\nCreating test user..."
    RANDOM_SUFFIX=$(date +%s%N | tail -c 8)
    USER_RESP=$(curl -X POST "${API_BASE}/users" \
        -H "Content-Type: application/json" \
        -d '{
            "email": "test-'"${RANDOM_SUFFIX}"'@example.com",
            "username": "testuser-'"${RANDOM_SUFFIX}"'",
            "password": "testpass123"
        }' -s)

    USER_ID=$(echo "$USER_RESP" | jq -r '.user.ID // empty')

    if [ -z "$USER_ID" ]; then
        echo -e "${RED}Failed to create test user. Response:${NC}"
        echo "$USER_RESP" | jq '.'
        exit 1
    fi

    echo -e "${GREEN}✓ Test user created: ${USER_ID}${NC}"
    echo -e "\nStarting tests in 2 seconds..."
    echo -e "Make sure API server and workers are running!"
    sleep 2

    test_1
    test_2
    test_3
    test_4
    test_5
    test_6
    test_7
    test_8
    test_9
    test_10

    echo -e "\n${GREEN}======================================================================${NC}"
    echo -e "${GREEN}All tests completed!${NC}"
    echo -e "${GREEN}======================================================================${NC}\n"
}

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo -e "${RED}Error: jq is required but not installed.${NC}"
    echo "Install with: brew install jq"
    exit 1
fi

main
