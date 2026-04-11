from app.users.user_model import User
from app.users.user_repository import UserRepository


def test_get_me(app, client, db_session, make_auth_header):
    repo = UserRepository(db_session)
    user = repo.create(User(email="me@example.com", display_name="Me"))
    db_session.commit()
    headers = make_auth_header(user.id)

    response = client.get("/users/me", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["email"] == "me@example.com"
    assert data["display_name"] == "Me"


def test_get_me_requires_auth(client):
    response = client.get("/users/me")
    assert response.status_code == 401
