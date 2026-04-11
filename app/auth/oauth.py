from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlencode

import requests

from app.exceptions import OAuthError


@dataclass
class OAuthUserInfo:
    email: str
    display_name: str
    avatar_url: str | None
    provider: str
    provider_id: str


class OAuthProvider(Protocol):
    def get_authorization_url(self, state: str) -> str: ...
    def exchange_code(self, code: str) -> OAuthUserInfo: ...


class GoogleOAuthProvider:
    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_authorization_url(self, state: str) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"

    def exchange_code(self, code: str) -> OAuthUserInfo:
        token_response = requests.post(
            self.TOKEN_URL,
            data={
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=10,
        )
        if token_response.status_code != 200:
            raise OAuthError(f"Google token exchange failed: {token_response.text}")

        access_token = token_response.json()["access_token"]

        userinfo_response = requests.get(
            self.USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        if userinfo_response.status_code != 200:
            raise OAuthError(f"Google userinfo failed: {userinfo_response.text}")

        data = userinfo_response.json()
        return OAuthUserInfo(
            email=data["email"],
            display_name=data.get("name", data["email"]),
            avatar_url=data.get("picture"),
            provider="google",
            provider_id=data["sub"],
        )


class GitHubOAuthProvider:
    AUTH_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    USER_URL = "https://api.github.com/user"
    EMAILS_URL = "https://api.github.com/user/emails"

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_authorization_url(self, state: str) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "user:email",
            "state": state,
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"

    def exchange_code(self, code: str) -> OAuthUserInfo:
        token_response = requests.post(
            self.TOKEN_URL,
            data={
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri,
            },
            headers={"Accept": "application/json"},
            timeout=10,
        )
        if token_response.status_code != 200:
            raise OAuthError(f"GitHub token exchange failed: {token_response.text}")

        access_token = token_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        user_response = requests.get(self.USER_URL, headers=headers, timeout=10)
        if user_response.status_code != 200:
            raise OAuthError(f"GitHub user fetch failed: {user_response.text}")
        user_data = user_response.json()

        email = user_data.get("email")
        if not email:
            emails_response = requests.get(self.EMAILS_URL, headers=headers, timeout=10)
            if emails_response.status_code == 200:
                for entry in emails_response.json():
                    if entry.get("primary") and entry.get("verified"):
                        email = entry["email"]
                        break
        if not email:
            raise OAuthError("Could not retrieve email from GitHub")

        return OAuthUserInfo(
            email=email,
            display_name=user_data.get("name") or user_data["login"],
            avatar_url=user_data.get("avatar_url"),
            provider="github",
            provider_id=str(user_data["id"]),
        )


class FakeOAuthProvider:
    """Test fake — returns preconfigured user info without hitting any external service."""

    def __init__(self, user_info: OAuthUserInfo):
        self.user_info = user_info

    def get_authorization_url(self, state: str) -> str:
        return f"http://fake-oauth/authorize?state={state}"

    def exchange_code(self, code: str) -> OAuthUserInfo:
        return self.user_info
