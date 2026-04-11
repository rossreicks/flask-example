import uuid

from flask import Blueprint, request

from app.auth.decorators import current_user_id, require_auth
from app.dependencies import get_message_service
from app.exceptions import NotAMemberError, ThreadNotFoundError

messages_bp = Blueprint("messages", __name__)


def _serialize_message(message):
    return {
        "id": str(message.id),
        "thread_id": str(message.thread_id),
        "user_id": str(message.user_id),
        "content": message.content,
        "created_at": message.created_at.isoformat(),
    }


@messages_bp.route("/threads/<thread_id>/messages", methods=["POST"])
@require_auth
def send_message(thread_id: str):
    data = request.get_json()
    service = get_message_service()
    try:
        message = service.send_message(
            user_id=current_user_id(),
            thread_id=uuid.UUID(thread_id),
            content=data["content"],
        )
    except ThreadNotFoundError:
        return {"error": "Thread not found"}, 404
    except NotAMemberError:
        return {"error": "Not a member of this thread"}, 403
    return _serialize_message(message), 201


@messages_bp.route("/threads/<thread_id>/messages", methods=["GET"])
@require_auth
def list_messages(thread_id: str):
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)
    service = get_message_service()
    try:
        messages = service.list_messages(thread_id=uuid.UUID(thread_id), limit=limit, offset=offset)
    except ThreadNotFoundError:
        return {"error": "Thread not found"}, 404
    return [_serialize_message(m) for m in messages]
