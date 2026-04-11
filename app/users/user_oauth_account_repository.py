import uuid

from sqlalchemy import select

from app.repositories import RepositorySession
from app.users.user_oauth_account_model import UserOAuthAccount


class UserOAuthAccountRepository:
    def __init__(self, session: RepositorySession):
        self.session = session

    def find_by_provider(self, provider: str, provider_id: str) -> UserOAuthAccount | None:
        stmt = select(UserOAuthAccount).where(
            UserOAuthAccount.provider == provider,
            UserOAuthAccount.provider_id == provider_id,
        )
        return self.session.scalar(stmt)

    def find_by_user_id(self, user_id: uuid.UUID) -> list[UserOAuthAccount]:
        stmt = select(UserOAuthAccount).where(UserOAuthAccount.user_id == user_id)
        return list(self.session.scalars(stmt))

    def create(self, account: UserOAuthAccount) -> UserOAuthAccount:
        self.session.add(account)
        self.session.flush()
        return account
