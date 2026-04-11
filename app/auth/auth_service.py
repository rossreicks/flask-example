from sqlalchemy.orm import Session

from app.auth.jwt import encode_token
from app.auth.oauth import OAuthProvider
from app.users.user_model import User
from app.users.user_oauth_account_model import UserOAuthAccount
from app.users.user_oauth_account_repository import UserOAuthAccountRepository
from app.users.user_repository import UserRepository


class AuthService:
    def __init__(
        self,
        provider: OAuthProvider,
        user_repo: UserRepository,
        oauth_account_repo: UserOAuthAccountRepository,
        session: Session,
        jwt_secret: str,
    ):
        self.provider = provider
        self.user_repo = user_repo
        self.oauth_account_repo = oauth_account_repo
        self.session = session
        self.jwt_secret = jwt_secret

    def login(self, code: str) -> tuple[str, User]:
        user_info = self.provider.exchange_code(code)

        existing_account = self.oauth_account_repo.find_by_provider(
            user_info.provider, user_info.provider_id
        )
        if existing_account:
            user = self.user_repo.find_by_id(existing_account.user_id)
            token = encode_token(user.id, self.jwt_secret)
            return token, user

        user = self.user_repo.find_by_email(user_info.email)
        if not user:
            user = self.user_repo.create(
                User(
                    email=user_info.email,
                    display_name=user_info.display_name,
                    avatar_url=user_info.avatar_url,
                )
            )

        self.oauth_account_repo.create(
            UserOAuthAccount(
                user_id=user.id,
                provider=user_info.provider,
                provider_id=user_info.provider_id,
            )
        )

        self.session.flush()
        token = encode_token(user.id, self.jwt_secret)
        return token, user
