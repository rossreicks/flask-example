import uuid

import jwt
import pytest
from testcontainers.postgres import PostgresContainer

from app import create_app
from app.config import TestConfig
from app.extensions import db as _db


@pytest.fixture(scope="session")
def postgres():
    with PostgresContainer("postgres:16", driver="psycopg2") as pg:
        yield pg


@pytest.fixture(scope="session")
def app(postgres):
    TestConfig.SQLALCHEMY_DATABASE_URI = postgres.get_connection_url()
    application = create_app(config=TestConfig)

    with application.app_context():
        _db.create_all()

    yield application

    with application.app_context():
        _db.drop_all()


@pytest.fixture
def db_session(app):
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()
        session = _db.session
        session.bind = connection

        yield session

        transaction.rollback()
        connection.close()
        session.remove()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def socketio_client(app):
    from app.extensions import socketio

    return socketio.test_client(app)


def make_jwt(user_id: uuid.UUID, app) -> str:
    return jwt.encode(
        {"sub": str(user_id)},
        app.config["JWT_SECRET"],
        algorithm="HS256",
    )


@pytest.fixture
def make_auth_header(app):
    def _make(user_id: uuid.UUID) -> dict:
        token = make_jwt(user_id, app)
        return {"Authorization": f"Bearer {token}"}

    return _make
