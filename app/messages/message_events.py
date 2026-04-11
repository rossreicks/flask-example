import uuid
from typing import Any, cast

from flask import current_app, g, request
from flask_socketio import emit, join_room

from app.auth.jwt import decode_token
from app.dependencies import get_message_service
from app.exceptions import NotAMemberError, ThreadNotFoundError
from app.extensions import socketio

_socket_user_ids: dict[str, uuid.UUID] = {}


def _socket_sid() -> str:
    """Flask-SocketIO sets ``sid`` on the request; it is absent from Werkzeug stubs."""
    return cast(Any, request).sid


@socketio.on("connect")
def handle_connect(_auth=None):
    token = request.headers.get("Authorization", "")
    if not token.startswith("Bearer "):
        return False
    try:
        user_id = decode_token(token[7:], current_app.config["JWT_SECRET"])
        g.current_user_id = user_id
        _socket_user_ids[_socket_sid()] = user_id
    except Exception:
        return False


@socketio.on("disconnect")
def handle_disconnect():
    _socket_user_ids.pop(_socket_sid(), None)


@socketio.on("join_thread")
def handle_join_thread(data):
    thread_id = data["thread_id"]
    join_room(thread_id)
    emit("thread_joined", {"thread_id": thread_id})


@socketio.on("send_message")
def handle_send_message(data):
    user_id = _socket_user_ids.get(_socket_sid()) or getattr(g, "current_user_id", None)
    if user_id is None:
        emit("error", {"message": "Unauthorized"})
        return

    service = get_message_service()
    try:
        message = service.send_message(
            user_id=user_id,
            thread_id=uuid.UUID(data["thread_id"]),
            content=data["content"],
        )
    except (ThreadNotFoundError, NotAMemberError) as e:
        emit("error", {"message": str(e)})
        return

    emit(
        "new_message",
        {
            "id": str(message.id),
            "thread_id": str(message.thread_id),
            "user_id": str(message.user_id),
            "content": message.content,
            "created_at": message.created_at.isoformat(),
        },
        to=data["thread_id"],
    )
