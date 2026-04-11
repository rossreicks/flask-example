import uuid

from sqlalchemy import select

from app.repositories import RepositorySession
from app.threads.thread_member_model import ThreadMember
from app.threads.thread_model import Thread


class ThreadRepository:
    def __init__(self, session: RepositorySession):
        self.session = session

    def find_by_id(self, thread_id: uuid.UUID) -> Thread | None:
        return self.session.get(Thread, thread_id)

    def create(self, thread: Thread) -> Thread:
        self.session.add(thread)
        self.session.flush()
        return thread

    def add_member(self, thread_id: uuid.UUID, user_id: uuid.UUID) -> ThreadMember:
        member = ThreadMember(thread_id=thread_id, user_id=user_id)
        self.session.add(member)
        self.session.flush()
        return member

    def is_member(self, thread_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        stmt = select(ThreadMember).where(
            ThreadMember.thread_id == thread_id,
            ThreadMember.user_id == user_id,
        )
        return self.session.scalar(stmt) is not None

    def list_members(self, thread_id: uuid.UUID) -> list[ThreadMember]:
        stmt = select(ThreadMember).where(ThreadMember.thread_id == thread_id)
        return list(self.session.scalars(stmt))

    def list_for_user(self, user_id: uuid.UUID) -> list[Thread]:
        stmt = (
            select(Thread)
            .join(ThreadMember, Thread.id == ThreadMember.thread_id)
            .where(ThreadMember.user_id == user_id)
        )
        return list(self.session.scalars(stmt))
