import uuid

from sqlalchemy import select

from app.repositories import RepositorySession
from app.users.user_model import User


class UserRepository:
    def __init__(self, session: RepositorySession):
        self.session = session

    def find_by_id(self, user_id: uuid.UUID) -> User | None:
        return self.session.get(User, user_id)

    def find_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return self.session.scalar(stmt)

    def create(self, user: User) -> User:
        self.session.add(user)
        self.session.flush()
        return user
