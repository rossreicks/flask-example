from app.auth.oauth import FakeOAuthProvider, OAuthUserInfo


def test_oauth_callback_creates_user_and_returns_jwt(app, client):
    fake_provider = FakeOAuthProvider(
        OAuthUserInfo(
            email="new@example.com",
            display_name="New User",
            avatar_url=None,
            provider="google",
            provider_id="g-999",
        )
    )
    app.config["_test_oauth_provider"] = fake_provider

    response = client.get("/auth/google/callback?code=fake-code&state=test")
    assert response.status_code == 200
    data = response.get_json()
    assert "token" in data
    assert data["user"]["email"] == "new@example.com"


def test_oauth_callback_returns_existing_user_on_second_login(app, client):
    fake_provider = FakeOAuthProvider(
        OAuthUserInfo(
            email="returning@example.com",
            display_name="Returning User",
            avatar_url=None,
            provider="google",
            provider_id="g-888",
        )
    )
    app.config["_test_oauth_provider"] = fake_provider

    response1 = client.get("/auth/google/callback?code=fake-code&state=test")
    response2 = client.get("/auth/google/callback?code=fake-code&state=test")

    data1 = response1.get_json()
    data2 = response2.get_json()
    assert data1["user"]["id"] == data2["user"]["id"]


def test_oauth_login_redirects(app, client):
    response = client.get("/auth/google/login")
    assert response.status_code == 302
