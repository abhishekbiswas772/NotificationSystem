from flask_smorest import Blueprint
from flask import request, jsonify
from handlers.notification_handler import NotificationHandler
from helpers.enums import MessageType, ProviderType, NotificationStatus
from dotenv import load_dotenv
import os

load_dotenv()

API_VERSION = os.getenv("API_VERSION", "/api/v1")
notification_blp = Blueprint("Notifications", __name__, "Notification Service")
notification_handler = NotificationHandler()


def _parse_enum(value, enum_cls):
    if value is None:
        return None
    try:
        if enum_cls.__name__ == "MessageType":
            return enum_cls(str(value).upper())
        if enum_cls.__name__ == "ProviderType":
            return enum_cls(str(value).upper())
        if enum_cls.__name__ == "NotificationStatus":
            return enum_cls(str(value).lower())
        return enum_cls(value)
    except ValueError:
        return None


@notification_blp.route(f"{API_VERSION}/notifications", methods=["POST"])
def create_notification():
    data = request.get_json() or {}
    user_id = data.get("user_id")
    payload = data.get("payload")
    message_type = _parse_enum(data.get("message_type"), MessageType)
    provider = _parse_enum(data.get("provider"), ProviderType)
    idempotency_key = data.get("idempotency_key")
    send_at = data.get("send_at")
    max_retries = data.get("max_retries")

    try:
        notification = notification_handler.create_notification(
            user_id=user_id,
            message_type=message_type,
            provider=provider,
            payload=payload,
            idempotency_key=idempotency_key,
            send_at=send_at,
            max_retries=max_retries,
        )
        return jsonify({"status": True, "data": notification.to_dict()}), 201
    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 400


@notification_blp.route(f"{API_VERSION}/notifications/bulk", methods=["POST"])
def bulk_create():
    items = request.get_json() or []
    try:
        created = notification_handler.bulk_create(items)
        return jsonify({
            "status": True,
            "data": [n.to_dict() for n in created],
        }), 201
    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 400


@notification_blp.route(f"{API_VERSION}/notifications/<string:notification_id>", methods=["GET"])
def get_notification(notification_id):
    try:
        notif = notification_handler.get_notification(notification_id)
        return jsonify({"status": True, "data": notif.to_dict()}), 200
    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 404


@notification_blp.route(f"{API_VERSION}/notifications", methods=["GET"])
def list_notifications():
    user_id = request.args.get("user_id")
    status = _parse_enum(request.args.get("status"), NotificationStatus)
    try:
        limit = int(request.args.get("limit", 20))
        offset = int(request.args.get("offset", 0))
    except ValueError:
        return jsonify({"status": False, "error": "limit and offset must be integers"}), 400

    try:
        notifs = notification_handler.list_notifications(
            user_id=user_id,
            status=status,
            limit=limit,
            offset=offset,
        )
        return jsonify({
            "status": True,
            "data": [n.to_dict() for n in notifs],
        }), 200
    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 400


@notification_blp.route(f"{API_VERSION}/notifications/<string:notification_id>", methods=["DELETE"])
def cancel_notification(notification_id):
    try:
        notification_handler.cancel_notification(notification_id)
        return jsonify({"status": True, "message": "cancelled"}), 200
    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 400
