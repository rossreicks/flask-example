import uuid

from flask import Blueprint, request

from app.auth.decorators import current_user_id, require_auth
from app.dependencies import get_thread_service
from app.exceptions import AlreadyAMemberError, ThreadNotFoundError

threads_bp = Blueprint("threads", __name__, url_prefix="/threads")


def _serialize_thread(thread):
    return {
        "id": str(thread.id),
        "name": thread.name,
        "created_by": str(thread.created_by),
        "created_at": thread.created_at.isoformat(),
    }


@threads_bp.route("", methods=["POST"])
@require_auth
def create_thread():
    data = request.get_json()
    service = get_thread_service()
    thread = service.create_thread(name=data["name"], user_id=current_user_id())
    return _serialize_thread(thread), 201


@threads_bp.route("", methods=["GET"])
@require_auth
def list_threads():
    service = get_thread_service()
    threads = service.list_threads(user_id=current_user_id())
    return [_serialize_thread(t) for t in threads]


@threads_bp.route("/<thread_id>/join", methods=["POST"])
@require_auth
def join_thread(thread_id: str):
    service = get_thread_service()
    try:
        service.join_thread(thread_id=uuid.UUID(thread_id), user_id=current_user_id())
    except ThreadNotFoundError:
        return {"error": "Thread not found"}, 404
    except AlreadyAMemberError:
        return {"error": "Already a member"}, 409
    return {"status": "joined"}
