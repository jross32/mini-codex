from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from .config import get_config
from .db import init_db, db_session
from .routes import register_routes

jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(get_config())
    CORS(
        app,
        resources={r"/*": {"origins": "*"}},
        supports_credentials=False,
        allow_headers="*",
        methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        expose_headers="*",
        send_wildcard=True,
        max_age=86400,
    )
    jwt.init_app(app)
    init_db(app)
    register_routes(app)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    return app
