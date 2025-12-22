#!/usr/bin/env python3
"""
Test all notification scenarios for Python implementation
Tests 10 different scenarios with local providers
"""

import requests
import json
import time
from datetime import datetime

API_BASE = "http://localhost:5000/api/v1"
USER_ID = "64cf1551-81b5-4199-913c-61a99e170540"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(num, name):
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.YELLOW}Test {num}/10: {name}{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}")

def print_success(msg):
    print(f"{Colors.GREEN}SUCCESS: {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}ERROR: {msg}{Colors.END}")

def create_notification(payload):
    """Create a notification via API"""
    try:
        response = requests.post(f"{API_BASE}/notifications", json=payload)
        if response.status_code in [200, 201]:
            data = response.json()
            if data.get('status'):
                print_success(f"Notification created: {data['data']['id']}")
                return data['data']
            else:
                print_error(f"Failed: {data.get('error')}")
                return None
        else:
            print_error(f"HTTP {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return None

def get_notification(notification_id):
    """Get notification status"""
    try:
        response = requests.get(f"{API_BASE}/notifications/{notification_id}")
        if response.status_code == 200:
            return response.json()['data']
        return None
    except:
        return None

def test_1_email_local():
    """Test 1: Send email via local provider"""
    print_test(1, "Email via Local Provider")

    payload = {
        "user_id": USER_ID,
        "message_type": "email",
        "provider": "local",
        "payload": json.dumps({
            "to": "user@example.com",
            "subject": "Test Email",
            "body": "<h1>Hello from Python Notification System!</h1>"
        }),
        "idempotency_key": f"test-1-{int(time.time())}"
    }

    result = create_notification(payload)
    if result:
        print_success(f"Status: {result['status']}")
        time.sleep(2)

def test_2_sms_console():
    """Test 2: Send SMS via console provider"""
    print_test(2, "SMS via Console Provider")

    payload = {
        "user_id": USER_ID,
        "message_type": "sms",
        "provider": "console_sms",
        "payload": json.dumps({
            "to": "+1234567890",
            "body": "Hello! This is a test SMS from Python Notification System."
        }),
        "idempotency_key": f"test-2-{int(time.time())}"
    }

    result = create_notification(payload)
    if result:
        print_success(f"Status: {result['status']}")
        time.sleep(2)

def test_3_push_local():
    """Test 3: Send push notification via local provider"""
    print_test(3, "Push Notification via Local Provider")

    payload = {
        "user_id": USER_ID,
        "message_type": "push",
        "provider": "local",
        "payload": json.dumps({
            "token": "device-token-123",
            "title": "New Message",
            "body": "You have a new notification!",
            "data": {"order_id": "12345"}
        }),
        "idempotency_key": f"test-3-{int(time.time())}"
    }

    result = create_notification(payload)
    if result:
        print_success(f"Status: {result['status']}")
        time.sleep(2)

def test_4_bulk_create():
    """Test 4: Bulk create notifications"""
    print_test(4, "Bulk Create (3 notifications)")

    notifications = [
        {
            "user_id": USER_ID,
            "message_type": "email",
            "provider": "local",
            "payload": json.dumps({"to": "user1@example.com", "subject": "Bulk 1", "body": "Message 1"}),
            "idempotency_key": f"bulk-1-{int(time.time())}"
        },
        {
            "user_id": USER_ID,
            "message_type": "sms",
            "provider": "console_sms",
            "payload": json.dumps({"to": "+1111111111", "body": "Bulk SMS 2"}),
            "idempotency_key": f"bulk-2-{int(time.time())}"
        },
        {
            "user_id": USER_ID,
            "message_type": "push",
            "provider": "local",
            "payload": json.dumps({"token": "token-3", "title": "Bulk 3", "body": "Message 3"}),
            "idempotency_key": f"bulk-3-{int(time.time())}"
        }
    ]

    try:
        response = requests.post(f"{API_BASE}/notifications/bulk", json=notifications)
        if response.status_code in [200, 201]:
            data = response.json()
            print_success(f"Created {len(data['data'])} notifications")
            time.sleep(3)
        else:
            print_error(f"Failed: {response.text}")
    except Exception as e:
        print_error(f"Error: {str(e)}")

def test_5_scheduled_notification():
    """Test 5: Schedule notification for future"""
    print_test(5, "Scheduled Notification (10 seconds from now)")

    future_time = int((time.time() + 10) * 1000)

    payload = {
        "user_id": USER_ID,
        "message_type": "email",
        "provider": "local",
        "payload": json.dumps({"to": "scheduled@example.com", "subject": "Scheduled", "body": "This was scheduled!"}),
        "send_at": future_time,
        "idempotency_key": f"test-5-{int(time.time())}"
    }

    result = create_notification(payload)
    if result:
        print_success(f"Scheduled for: {datetime.fromtimestamp(future_time/1000)}")

def test_6_idempotency():
    """Test 6: Idempotency - duplicate detection"""
    print_test(6, "Idempotency (send same notification twice)")

    idempotency_key = f"duplicate-test-{int(time.time())}"

    payload = {
        "user_id": USER_ID,
        "message_type": "email",
        "provider": "local",
        "payload": json.dumps({"to": "duplicate@example.com", "subject": "Duplicate", "body": "Test"}),
        "idempotency_key": idempotency_key
    }

    print("  Attempt 1:")
    result1 = create_notification(payload)

    time.sleep(1)

    print("\n  Attempt 2 (should fail):")
    result2 = create_notification(payload)

    if result1 and not result2:
        print_success("Idempotency working correctly!")

def test_7_list_notifications():
    """Test 7: List notifications"""
    print_test(7, "List User Notifications")

    try:
        response = requests.get(f"{API_BASE}/notifications", params={
            "user_id": USER_ID,
            "limit": 10
        })

        if response.status_code == 200:
            data = response.json()
            notifications = data.get('data', [])
            print_success(f"Found {len(notifications)} notifications for user {USER_ID}")

            for notif in notifications[:3]:
                print(f"  - ID: {notif['id']}, Status: {notif['status']}, Type: {notif['message_type']}")
        else:
            print_error(f"Failed: {response.text}")
    except Exception as e:
        print_error(f"Error: {str(e)}")

def test_8_cancel_notification():
    """Test 8: Cancel pending notification"""
    print_test(8, "Cancel Notification")

    future_time = int((time.time() + 60) * 1000)
    payload = {
        "user_id": USER_ID,
        "message_type": "email",
        "provider": "local",
        "payload": json.dumps({"to": "cancel@example.com", "subject": "To Cancel", "body": "This will be cancelled"}),
        "send_at": future_time,
        "idempotency_key": f"cancel-test-{int(time.time())}"
    }

    result = create_notification(payload)
    if result:
        notification_id = result['id']
        time.sleep(1)

        try:
            response = requests.delete(f"{API_BASE}/notifications/{notification_id}")
            if response.status_code == 200:
                print_success(f"Notification {notification_id} cancelled successfully")
            else:
                print_error(f"Failed to cancel: {response.text}")
        except Exception as e:
            print_error(f"Error: {str(e)}")

def test_9_get_notification():
    """Test 9: Get single notification"""
    print_test(9, "Get Single Notification")

    payload = {
        "user_id": USER_ID,
        "message_type": "sms",
        "provider": "console_sms",
        "payload": json.dumps({"to": "+9999999999", "body": "Get test"}),
        "idempotency_key": f"get-test-{int(time.time())}"
    }

    result = create_notification(payload)
    if result:
        notification_id = result['id']
        time.sleep(2)

        try:
            response = requests.get(f"{API_BASE}/notifications/{notification_id}")
            if response.status_code == 200:
                data = response.json()['data']
                print_success(f"Retrieved notification: {notification_id}")
                print(f"  Status: {data['status']}")
                print(f"  Type: {data['message_type']}")
                print(f"  Provider: {data['provider']}")
                print(f"  Attempts: {data.get('attempt_count', 0)}")
            else:
                print_error(f"Failed: {response.text}")
        except Exception as e:
            print_error(f"Error: {str(e)}")

def test_10_max_retries():
    """Test 10: Test retry mechanism (simulated failure)"""
    print_test(10, "Retry Mechanism (Multiple Notifications)")

    for i in range(5):
        payload = {
            "user_id": USER_ID,
            "message_type": "email" if i % 2 == 0 else "sms",
            "provider": "local" if i % 2 == 0 else "console_sms",
            "payload": json.dumps({
                "to": f"retry{i}@example.com" if i % 2 == 0 else f"+{i*111}",
                "subject": f"Retry Test {i}" if i % 2 == 0 else None,
                "body": f"Testing retry queue system - Message {i+1}"
            }),
            "max_retries": 3,
            "idempotency_key": f"retry-test-{i}-{int(time.time())}"
        }

        result = create_notification(payload)
        if result:
            print(f"  Created notification {i+1}/5")
        time.sleep(0.5)

    print_success("Created 5 notifications to test queue processing")
    print("  Check worker logs to see processing...")

if __name__ == "__main__":
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.YELLOW}Python Notification System - Comprehensive Test Suite{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"\nAPI Base: {API_BASE}")
    print(f"User ID: {USER_ID}")
    print(f"\nStarting tests in 2 seconds...")
    print(f"Make sure API server and workers are running!")
    time.sleep(2)

    try:
        test_1_email_local()
        time.sleep(1)

        test_2_sms_console()
        time.sleep(1)

        test_3_push_local()
        time.sleep(1)

        test_4_bulk_create()
        time.sleep(1)

        test_5_scheduled_notification()
        time.sleep(1)

        test_6_idempotency()
        time.sleep(1)

        test_7_list_notifications()
        time.sleep(1)

        test_8_cancel_notification()
        time.sleep(1)

        test_9_get_notification()
        time.sleep(1)

        test_10_max_retries()

        print(f"\n{Colors.GREEN}{'='*70}{Colors.END}")
        print(f"{Colors.GREEN}All tests completed!{Colors.END}")
        print(f"{Colors.GREEN}{'='*70}{Colors.END}\n")

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}Test suite error: {str(e)}{Colors.END}")
