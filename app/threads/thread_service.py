import uuid

from sqlalchemy.orm import Session

from app.exceptions import AlreadyAMemberError, ThreadNotFoundError
from app.threads.thread_model import Thread
from app.threads.thread_repository import ThreadRepository


class ThreadService:
    def __init__(self, thread_repo: ThreadRepository, session: Session):
        self.thread_repo = thread_repo
        self.session = session

    def create_thread(self, name: str, user_id: uuid.UUID) -> Thread:
        thread = self.thread_repo.create(Thread(name=name, created_by=user_id))
        self.thread_repo.add_member(thread.id, user_id)
        self.session.commit()
        return thread

    def join_thread(self, thread_id: uuid.UUID, user_id: uuid.UUID) -> None:
        thread = self.thread_repo.find_by_id(thread_id)
        if not thread:
            raise ThreadNotFoundError(thread_id)
        if self.thread_repo.is_member(thread_id, user_id):
            raise AlreadyAMemberError(user_id, thread_id)
        self.thread_repo.add_member(thread_id, user_id)
        self.session.commit()

    def list_threads(self, user_id: uuid.UUID) -> list[Thread]:
        return self.thread_repo.list_for_user(user_id)

    def get_thread(self, thread_id: uuid.UUID) -> Thread:
        thread = self.thread_repo.find_by_id(thread_id)
        if not thread:
            raise ThreadNotFoundError(thread_id)
        return thread
