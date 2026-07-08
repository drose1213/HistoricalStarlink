"""SMTP authentication behavior tests."""

from backend.routers import auth


class FakeSMTP:
    def __init__(self) -> None:
        self.esmtp_features = {"auth": "LOGIN PLAIN XOAUTH2"}
        self.login_called = False
        self.auth_calls: list[str] = []

    def auth(self, mechanism: str, authobject) -> tuple[int, bytes]:
        self.auth_calls.append(mechanism)
        return 235, b"Authentication successful"

    def auth_login(self, challenge=None) -> str:
        return "auth-response"

    def login(self, username: str, password: str) -> tuple[int, bytes]:
        self.login_called = True
        return 235, b"fallback login"


def test_login_smtp_prefers_auth_login_when_supported(monkeypatch):
    monkeypatch.setattr(auth.settings, "SMTP_USER", "user@example.com")
    monkeypatch.setattr(auth.settings, "SMTP_PASSWORD", "secret")
    smtp = FakeSMTP()

    auth._login_smtp(smtp)

    assert smtp.auth_calls == ["LOGIN"]
    assert smtp.login_called is False
