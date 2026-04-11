import secrets

from flask import Blueprint, current_app, redirect, request

from app.dependencies import get_auth_service, get_oauth_provider
from app.extensions import db

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _serialize_user(user):
    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
        "avatar_url": user.avatar_url,
    }


@auth_bp.route("/<provider_name>/login")
def oauth_login(provider_name: str):
    provider = get_oauth_provider(provider_name)
    state = secrets.token_urlsafe(32)
    url = provider.get_authorization_url(state)
    return redirect(url)


@auth_bp.route("/<provider_name>/callback")
def oauth_callback(provider_name: str):
    code = request.args.get("code")
    if not code:
        return {"error": "Missing code parameter"}, 400

    test_provider = current_app.config.get("_test_oauth_provider")
    provider = test_provider or get_oauth_provider(provider_name)

    service = get_auth_service(provider=provider)
    token, user = service.login(code=code)
    db.session.commit()

    return {"token": token, "user": _serialize_user(user)}
