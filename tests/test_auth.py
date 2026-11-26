from types import SimpleNamespace

import pytest

from app import create_app


class FakeAuth:
    def __init__(self):
        self.current_session = None
        self.signed_out = False
        self.sign_out_options = None

    def sign_up(self, credentials):
        return SimpleNamespace(user=SimpleNamespace(id="user-123", email=credentials["email"]), session=None)

    def sign_in_with_password(self, credentials):
        auth_session = SimpleNamespace(access_token="access-token", refresh_token="refresh-token")
        user = SimpleNamespace(id="user-123", email=credentials["email"])
        self.current_session = auth_session
        return SimpleNamespace(session=auth_session, user=user)

    def set_session(self, access_token, refresh_token):
        self.current_session = SimpleNamespace(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    def get_session(self):
        return self.current_session

    def sign_out(self, options=None):
        self.signed_out = True
        self.sign_out_options = options


class FakeQuery:
    def select(self, *_args):
        return self

    def eq(self, *_args):
        return self

    def order(self, *_args):
        return self

    def execute(self):
        return SimpleNamespace(data=[])


class FakeClient:
    def __init__(self):
        self.auth = FakeAuth()

    def table(self, _table_name):
        return FakeQuery()


@pytest.fixture
def app(tmp_path):
    return create_app(
        {
            "TESTING": True,
            "APP_ENV": "test",
            "SECRET_KEY": "test-secret-key-that-is-long-enough",
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_PUBLISHABLE_KEY": "test-publishable-key",
            "SESSION_FILE_DIR": str(tmp_path / "sessions"),
            "WTF_CSRF_ENABLED": False,
            "SUPABASE_CLIENT_FACTORY": lambda _url, _key: FakeClient(),
        }
    )


def test_wishes_requires_authentication(app):
    response = app.test_client().get("/wishes")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_login_creates_a_server_side_session_and_opens_wishlist(app):
    client = app.test_client()

    response = client.post(
        "/login",
        data={"email": "person@example.com", "password": "safe-password"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/wishes")
    wishlist_response = client.get("/wishes")
    assert wishlist_response.status_code == 200
    assert b"person@example.com" in wishlist_response.data


def test_sign_out_revokes_only_the_current_session(app):
    clients = []

    def make_client(_url, _key):
        client = FakeClient()
        clients.append(client)
        return client

    app.config["SUPABASE_CLIENT_FACTORY"] = make_client
    browser = app.test_client()
    browser.post(
        "/login",
        data={"email": "person@example.com", "password": "safe-password"},
    )

    response = browser.post("/logout")

    assert response.status_code == 302
    assert clients[-1].auth.sign_out_options == {"scope": "local"}


def test_signup_requires_matching_passwords(app):
    response = app.test_client().post(
        "/signup",
        data={
            "email": "person@example.com",
            "password": "safe-password",
            "password_confirmation": "different-password",
        },
    )

    assert response.status_code == 200
    assert b"The passwords do not match." in response.data


@pytest.mark.parametrize(
    ("locale", "expected_text"),
    [
        ("es", "Crear cuenta"),
        ("fr", "Créer un compte"),
        ("de", "Konto erstellen"),
        ("en", "Create account"),
    ],
)
def test_language_preference_changes_the_auth_page(app, locale, expected_text):
    client = app.test_client()
    response = client.post(
        "/language",
        data={"locale": locale, "next": "/signup"},
    )

    assert response.status_code == 302
    signup_page = client.get("/signup")
    assert expected_text.encode() in signup_page.data


def test_language_route_rejects_external_redirects(app):
    response = app.test_client().post(
        "/language",
        data={"locale": "de", "next": "//example.com/"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_production_requires_a_redis_session_store():
    with pytest.raises(RuntimeError, match="SESSION_REDIS_URL"):
        create_app(
            {
                "APP_ENV": "production",
                "SECRET_KEY": "a-production-secret-that-is-at-least-32-characters",
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_PUBLISHABLE_KEY": "test-publishable-key",
            }
        )
