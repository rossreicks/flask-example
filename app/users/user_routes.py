from flask import Blueprint

from app.auth.decorators import current_user_id, require_auth
from app.dependencies import get_user_service
from app.exceptions import UserNotFoundError

users_bp = Blueprint("users", __name__, url_prefix="/users")


def _serialize_user(user):
    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
        "avatar_url": user.avatar_url,
    }


@users_bp.route("/me", methods=["GET"])
@require_auth
def get_me():
    service = get_user_service()
    try:
        user = service.get_me(current_user_id())
    except UserNotFoundError:
        return {"error": "User not found"}, 404
    return _serialize_user(user)
