"""Phase 1 regression tests. Run with: pytest -q"""
import io
import pytest

from app import app
from models import db, User


@pytest.fixture()
def client():
    app.config.update(TESTING=True, SECRET_KEY="test-only-secret", WTF_CSRF_ENABLED=False,
                      SQLALCHEMY_DATABASE_URI="sqlite:///toolforge_test.db")
    with app.app_context():
        db.drop_all()
        db.create_all()
        user = User(name="Test User", email="test@example.com", role="user", is_active=True)
        user.set_password("test-password-123")
        db.session.add(user)
        db.session.commit()
    with app.test_client() as test_client:
        yield test_client
    with app.app_context():
        db.session.remove()
        db.drop_all()


def sign_in(client):
    with client.session_transaction() as session:
        session["user_id"] = 1
        session["user_name"] = "Test User"
        session["user_email"] = "test@example.com"
        session["user_role"] = "user"


def test_tool_pages_require_session(client):
    response = client.get("/")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_api_requires_session(client):
    response = client.get("/api/translation-status")
    assert response.status_code == 401
    assert response.get_json()["login_required"] is True


def test_signed_in_api_remains_available(client):
    sign_in(client)
    response = client.get("/api/translation-status")
    assert response.status_code == 200


def test_pdf_endpoint_rejects_wrong_extension(client):
    sign_in(client)
    response = client.post(
        "/api/pdf/split",
        data={"file": (io.BytesIO(b"not a pdf"), "notes.txt")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 415


def test_pdf_endpoint_rejects_invalid_pdf_content(client):
    sign_in(client)
    response = client.post(
        "/api/pdf/split",
        data={"file": (io.BytesIO(b"this is not a pdf"), "notes.pdf")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400


def test_registration_creates_hashed_user_account(client):
    response = client.post("/register", data={
        "name": "New User",
        "email": "new@example.com",
        "password": "a-strong-password-123",
        "confirm_password": "a-strong-password-123",
    }, follow_redirects=False)
    assert response.status_code == 302
    with app.app_context():
        user = User.query.filter_by(email="new@example.com").first()
        assert user is not None
        assert user.role == "user"
        assert user.password_hash != "a-strong-password-123"
        assert user.check_password("a-strong-password-123")


def test_login_rejects_wrong_password(client):
    response = client.post("/login", data={
        "email": "test@example.com",
        "password": "wrong-password",
    })
    assert response.status_code == 200
    assert b"Invalid email or password" in response.data


def test_normal_user_cannot_open_admin_dashboard(client):
    sign_in(client)
    response = client.get("/admin")
    assert response.status_code == 403
