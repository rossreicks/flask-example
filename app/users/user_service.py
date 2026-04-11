import uuid

from app.exceptions import UserNotFoundError
from app.users.user_model import User
from app.users.user_repository import UserRepository


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def get_user(self, user_id: uuid.UUID) -> User:
        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        return user

    def get_me(self, user_id: uuid.UUID) -> User:
        return self.get_user(user_id)
