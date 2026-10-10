from flask import Flask
from flask_cors import CORS

from app.config import Config
from app.extensions import db, jwt
from app.utils.errors import register_error_handlers


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    jwt.init_app(app)
    allowed_origins = [origin.strip() for origin in app.config["FRONTEND_ORIGIN"].split(",")]
    CORS(app, origins=allowed_origins)

    from app import models

    register_error_handlers(app)

    from app.routes.health import health_bp
    from app.routes.auth import auth_bp
    from app.routes.policies import policies_bp
    from app.routes.hospitals import hospitals_bp
    from app.routes.claims import claims_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.users import users_bp

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(policies_bp, url_prefix="/api/policies")
    app.register_blueprint(hospitals_bp, url_prefix="/api/hospitals")
    app.register_blueprint(claims_bp, url_prefix="/api/claims")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(users_bp, url_prefix="/api/users")

    return app
