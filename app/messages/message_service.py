import uuid

from sqlalchemy.orm import Session

from app.exceptions import NotAMemberError, ThreadNotFoundError
from app.messages.message_model import Message
from app.messages.message_repository import MessageRepository
from app.threads.thread_repository import ThreadRepository


class MessageService:
    def __init__(
        self,
        message_repo: MessageRepository,
        thread_repo: ThreadRepository,
        session: Session,
    ):
        self.message_repo = message_repo
        self.thread_repo = thread_repo
        self.session = session

    def send_message(self, user_id: uuid.UUID, thread_id: uuid.UUID, content: str) -> Message:
        thread = self.thread_repo.find_by_id(thread_id)
        if not thread:
            raise ThreadNotFoundError(thread_id)
        if not self.thread_repo.is_member(thread_id, user_id):
            raise NotAMemberError(user_id, thread_id)

        message = self.message_repo.create(
            Message(thread_id=thread_id, user_id=user_id, content=content)
        )
        self.session.commit()
        return message

    def list_messages(
        self, thread_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[Message]:
        thread = self.thread_repo.find_by_id(thread_id)
        if not thread:
            raise ThreadNotFoundError(thread_id)
        return self.message_repo.list_by_thread(thread_id, limit=limit, offset=offset)
