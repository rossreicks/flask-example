from flask import Flask

from app.config import DevConfig
from app.extensions import db, migrate, socketio


def create_app(config=None):
    flask_app = Flask(__name__)
    flask_app.config.from_object(config or DevConfig)

    db.init_app(flask_app)
    migrate.init_app(flask_app, db)
    socketio.init_app(flask_app, cors_allowed_origins="*")

    with flask_app.app_context():
        import app.messages.message_model  # noqa: F401
        import app.threads.thread_member_model  # noqa: F401
        import app.threads.thread_model  # noqa: F401
        import app.users.user_model  # noqa: F401
        import app.users.user_oauth_account_model  # noqa: F401

    from app.auth.auth_routes import auth_bp
    from app.messages.message_routes import messages_bp
    from app.threads.thread_routes import threads_bp
    from app.users.user_routes import users_bp

    flask_app.register_blueprint(auth_bp)
    flask_app.register_blueprint(threads_bp)
    flask_app.register_blueprint(messages_bp)
    flask_app.register_blueprint(users_bp)

    import app.messages.message_events  # noqa: F401, E402

    return flask_app
