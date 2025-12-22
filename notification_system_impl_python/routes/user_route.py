from flask_smorest import Blueprint
from flask import request, jsonify
from handlers.user_handlers import UserHandler
from dotenv import load_dotenv
import os

load_dotenv()

API_VERSION = os.getenv("API_VERSION", "/api/v1")
user_blp = Blueprint("Users", __name__, "User Service")
user_handler = UserHandler()


@user_blp.route(f"{API_VERSION}/users", methods = ["POST"])
def login_user():
    data = request.get_json()
    username = data.get("username", "")
    password = data.get("password", "")
    try:
        user = user_handler.login_user(username=username, password=password)
        if not user:
            return jsonify({
                "status" : False,
                "error" : "failed to create user"
            }), 400
        return jsonify({
            "status" : True,
            "data" : user.to_dict()
        }), 201
    except Exception as e:
        print(e)
        return jsonify({
            "status" : False,
            "error" : str(e),
            "message" : "Internal Server Error"
        }), 500 


@user_blp.route(f"{API_VERSION}/users", methods = ["POST"])
def create_user():
    data = request.get_json()
    username = data.get("username", "")
    password = data.get("password", "")
    email = data.get("email", "")

    try:
        user = user_handler.create_user(username=username, password=password, email=email)
        if not user:
            return jsonify({
                "status" : False,
                "error" : "failed to create user"
            }), 400
        return jsonify({
            "status" : True,
            "data" : user.to_dict()
        }), 201
    except Exception as e:
        print(e)
        return jsonify({
            "status" : False,
            "error" : str(e),
            "message" : "Internal Server Error"
        }), 500