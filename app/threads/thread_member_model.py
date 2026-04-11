from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

if TYPE_CHECKING:
    from app.threads.thread_model import Thread
    from app.users.user_model import User


class ThreadMember(db.Model):
    __tablename__ = "thread_members"

    thread_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("threads.id"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    joined_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)

    thread: Mapped[Thread] = relationship(back_populates="members")
    user: Mapped[User] = relationship()
