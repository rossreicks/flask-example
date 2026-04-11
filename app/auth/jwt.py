import uuid
from datetime import UTC, datetime, timedelta

import jwt as pyjwt


def encode_token(user_id: uuid.UUID, secret: str, expires_in: int = 86400) -> str:
    payload = {
        "sub": str(user_id),
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(seconds=expires_in),
    }
    return pyjwt.encode(payload, secret, algorithm="HS256")


def decode_token(token: str, secret: str) -> uuid.UUID:
    payload = pyjwt.decode(token, secret, algorithms=["HS256"])
    return uuid.UUID(payload["sub"])
