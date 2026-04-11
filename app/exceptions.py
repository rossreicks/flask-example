import uuid


class NotFoundError(Exception):
    def __init__(self, entity: str, entity_id: uuid.UUID):
        self.entity = entity
        self.entity_id = entity_id
        super().__init__(f"{entity} {entity_id} not found")


class UserNotFoundError(NotFoundError):
    def __init__(self, user_id: uuid.UUID):
        super().__init__("User", user_id)


class ThreadNotFoundError(NotFoundError):
    def __init__(self, thread_id: uuid.UUID):
        super().__init__("Thread", thread_id)


class NotAMemberError(Exception):
    def __init__(self, user_id: uuid.UUID, thread_id: uuid.UUID):
        self.user_id = user_id
        self.thread_id = thread_id
        super().__init__(f"User {user_id} is not a member of thread {thread_id}")


class AlreadyAMemberError(Exception):
    def __init__(self, user_id: uuid.UUID, thread_id: uuid.UUID):
        self.user_id = user_id
        self.thread_id = thread_id
        super().__init__(f"User {user_id} is already a member of thread {thread_id}")


class OAuthError(Exception):
    pass
