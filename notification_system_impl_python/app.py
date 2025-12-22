from flask import Flask
from flask_smorest import Api
from configs.db import db
from routes.user_route import user_blp
from routes.notification_route import notification_blp
import os
from dotenv import load_dotenv

from models import (
    users,
    api_keys,
    audit_logs,
    notification_metrics,
    notification_preferences,
    notification_template,
    notification_webhook,
    notification,
    notification_dlq,
    provider_config,
    rate_limit,
    webhook_delivery,
)

load_dotenv()

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.secret_key = os.getenv("FLASK_KEY")
    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["API_TITLE"] = "Notification REST API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    api = Api(app)
    db.init_app(app)

    with app.app_context():
        db.create_all()
    api.register_blueprint(user_blp)
    api.register_blueprint(notification_blp)
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
