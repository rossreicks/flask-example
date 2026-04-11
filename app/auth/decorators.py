import functools
import uuid

from flask import current_app, g, request
from flask_socketio import disconnect

from app.auth.jwt import decode_token


def _extract_user_id() -> uuid.UUID | None:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]
    try:
        return decode_token(token, current_app.config["JWT_SECRET"])
    except Exception:
        return None


def require_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        user_id = _extract_user_id()
        if user_id is None:
            return {"error": "Unauthorized"}, 401
        g.current_user_id = user_id
        return f(*args, **kwargs)

    return decorated


def current_user_id() -> uuid.UUID:
    return g.current_user_id


def require_socket_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        user_id = _extract_user_id()
        if user_id is None:
            disconnect()
            return
        g.current_user_id = user_id
        return f(*args, **kwargs)

    return decorated
