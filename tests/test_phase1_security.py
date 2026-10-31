"""Phase 1 regression tests. Run with: pytest -q"""
import io
import pytest

import app as app_module
from app import app


@pytest.fixture()
def client():
    app.config.update(TESTING=True, SECRET_KEY="test-only-secret")
    with app.test_client() as client:
        yield client


def sign_in(client):
    with client.session_transaction() as session:
        session["user_name"] = "Test User"
        session["user_email"] = "test@example.com"


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


def test_tts_rejects_unknown_language_instead_of_silently_using_english(client):
    sign_in(client)
    response = client.post("/api/tts", json={"text": "Hello", "lang": "Not a language"})
    assert response.status_code == 400
    assert "valid speech language" in response.get_json()["error"]


def test_tts_maps_simplified_chinese_to_regional_voice_code(client, monkeypatch):
    sign_in(client)
    seen = {}

    def fake_audio(text, code):
        seen["text"] = text
        seen["code"] = code
        return "ZmFrZS1hdWRpbw=="

    monkeypatch.setattr(app_module, "get_tts_audio_b64", fake_audio)
    response = client.post(
        "/api/tts", json={"text": "你好", "lang": "Chinese (Simplified)"}
    )
    assert response.status_code == 200
    assert seen == {"text": "你好", "code": "zh"}
    assert response.get_json()["mime"] == "audio/mpeg"
