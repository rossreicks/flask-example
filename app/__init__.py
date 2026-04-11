from flask import Flask

from app.config import DevConfig
from app.extensions import db, migrate, socketio


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(config or DevConfig)

    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins="*")

    return app
