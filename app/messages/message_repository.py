import uuid

from sqlalchemy import select

from app.messages.message_model import Message
from app.repositories import RepositorySession


class MessageRepository:
    def __init__(self, session: RepositorySession):
        self.session = session

    def find_by_id(self, message_id: uuid.UUID) -> Message | None:
        return self.session.get(Message, message_id)

    def create(self, message: Message) -> Message:
        self.session.add(message)
        self.session.flush()
        return message

    def list_by_thread(
        self, thread_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[Message]:
        stmt = (
            select(Message)
            .where(Message.thread_id == thread_id)
            .order_by(Message.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(stmt))
