"""用户认证 API 黑盒测试"""
import smtplib

import pytest


@pytest.mark.e2e
class TestAuthAPI:
    """测试 /api/auth 系列接口"""

    async def test_register_new_user_with_code(self, client, test_db):
        """通过预填验证码注册新用户"""
        from backend.redis_client import cache
        from backend.config import settings
        # 直接往 cache 写验证码
        await cache.set("email_code:test_new@example.com", "123456", 300)

        res = await client.post("/api/auth/register", json={
            "username": "testnew",
            "email": "test_new@example.com",
            "email_code": "123456",
            "password": "Test123456",
        })
        assert res.status_code == 200
        body = res.json()
        assert body["code"] == 200
        assert "token" in body["data"]
        assert body["data"]["user"]["username"] == "testnew"

    async def test_register_invalid_email_code(self, client, test_db):
        from backend.redis_client import cache
        await cache.set("email_code:test_invalid@example.com", "654321", 300)

        res = await client.post("/api/auth/register", json={
            "username": "testinvalid",
            "email": "test_invalid@example.com",
            "email_code": "123456",  # 错误验证码
            "password": "Test123456",
        })
        assert res.status_code == 400

    async def test_register_expired_code(self, client, test_db):
        # 不写入验证码或写入后过期
        res = await client.post("/api/auth/register", json={
            "username": "testexpired",
            "email": "test_expired@example.com",
            "email_code": "123456",
            "password": "Test123456",
        })
        assert res.status_code == 400

    async def test_register_validation_errors(self, client, test_db):
        """注册参数验证"""
        # 用户名太短
        res = await client.post("/api/auth/register", json={
            "username": "ab",
            "email": "test@example.com",
            "email_code": "123456",
            "password": "Test123456",
        })
        assert res.status_code in (400, 422)

        # 邮箱格式错误
        res = await client.post("/api/auth/register", json={
            "username": "validname",
            "email": "not_an_email",
            "email_code": "123456",
            "password": "Test123456",
        })
        assert res.status_code in (400, 422)

        # 密码太短
        res = await client.post("/api/auth/register", json={
            "username": "validname2",
            "email": "valid@example.com",
            "email_code": "123456",
            "password": "123",
        })
        assert res.status_code in (400, 422)

    async def test_login_success(self, client, test_db, auth_token):
        """已存在用户登录"""
        res = await client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "Test123456",
        })
        assert res.status_code == 200
        body = res.json()
        assert "token" in body["data"]

    async def test_login_wrong_password(self, client, test_db, auth_token):
        res = await client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "WrongPassword",
        })
        assert res.status_code == 401

    async def test_send_password_reset_code_for_registered_email(self, client, test_db, auth_token, monkeypatch):
        """申请重置密码验证码时，为已注册邮箱写入独立的 reset code"""
        from backend.config import settings
        from backend.redis_client import cache
        from backend.routers import auth as auth_router

        monkeypatch.setattr(settings, "SMTP_USER", "smtp@example.com")
        monkeypatch.setattr(settings, "SMTP_PASSWORD", "smtp-secret")

        async def fake_send_email(to_email: str, code: str) -> None:
            assert to_email == "test@example.com"
            assert code.isdigit()

        monkeypatch.setattr(auth_router, "_send_email", fake_send_email)

        res = await client.post("/api/auth/password-reset/send-code", json={
            "email": "test@example.com",
        })
        assert res.status_code == 200

        stored_code = await cache.get("password_reset_code:test@example.com")
        assert isinstance(stored_code, str)
        assert len(stored_code) == 6
        assert stored_code.isdigit()

    async def test_send_password_reset_code_reports_smtp_failure(self, client, test_db, auth_token, monkeypatch):
        """SMTP failure should not return false success or cache a reset code."""
        from backend.config import settings
        from backend.redis_client import cache
        from backend.routers import auth as auth_router

        monkeypatch.setattr(settings, "SMTP_USER", "smtp@example.com")
        monkeypatch.setattr(settings, "SMTP_PASSWORD", "smtp-secret")

        async def fake_send_email(to_email: str, code: str) -> None:
            raise smtplib.SMTPServerDisconnected("Connection unexpectedly closed")

        monkeypatch.setattr(auth_router, "_send_email", fake_send_email)

        res = await client.post("/api/auth/password-reset/send-code", json={
            "email": "test@example.com",
        })

        assert res.status_code == 502
        assert await cache.get("password_reset_code:test@example.com") is None
        assert not await cache.exists("password_reset_code_cd:test@example.com")

    async def test_send_password_reset_code_reports_smtp_auth_failure_detail(self, client, test_db, auth_token, monkeypatch):
        """SMTP auth failures should expose an actionable but non-secret message."""
        from backend.config import settings
        from backend.routers import auth as auth_router

        monkeypatch.setattr(settings, "SMTP_USER", "smtp@example.com")
        monkeypatch.setattr(settings, "SMTP_PASSWORD", "smtp-secret")

        async def fake_send_email(to_email: str, code: str) -> None:
            raise smtplib.SMTPAuthenticationError(535, b"Login fail")

        monkeypatch.setattr(auth_router, "_send_email", fake_send_email)

        res = await client.post("/api/auth/password-reset/send-code", json={
            "email": "test@example.com",
        })

        assert res.status_code == 502
        assert "SMTP 登录失败" in res.json()["detail"]
        assert "授权码" in res.json()["detail"]

    async def test_reset_password_with_email_code(self, client, test_db, auth_token):
        """邮箱验证码重置密码后旧密码失效，新密码可登录"""
        from backend.redis_client import cache

        await cache.set("password_reset_code:test@example.com", "778899", 300)

        reset_res = await client.post("/api/auth/password-reset/confirm", json={
            "email": "test@example.com",
            "email_code": "778899",
            "new_password": "NewTest123456",
        })
        assert reset_res.status_code == 200

        old_login = await client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "Test123456",
        })
        assert old_login.status_code == 401

        new_login = await client.post("/api/auth/login", json={
            "username": "test@example.com",
            "password": "NewTest123456",
        })
        assert new_login.status_code == 200
        assert "token" in new_login.json()["data"]

        assert await cache.get("password_reset_code:test@example.com") is None

    async def test_reset_password_rejects_invalid_code(self, client, test_db, auth_token):
        """错误的邮箱验证码不能重置密码"""
        from backend.redis_client import cache

        await cache.set("password_reset_code:test@example.com", "111222", 300)

        reset_res = await client.post("/api/auth/password-reset/confirm", json={
            "email": "test@example.com",
            "email_code": "000000",
            "new_password": "NewTest123456",
        })
        assert reset_res.status_code == 400

        login_res = await client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "Test123456",
        })
        assert login_res.status_code == 200

    async def test_login_nonexistent_user(self, client, test_db):
        res = await client.post("/api/auth/login", json={
            "username": "nonexistent_user_xyz",
            "password": "any",
        })
        assert res.status_code == 404

    async def test_get_me_with_token(self, client, test_db, auth_headers):
        res = await client.get("/api/auth/me", headers=auth_headers)
        assert res.status_code == 200
        body = res.json()
        assert body["data"]["username"] == "testuser"

    async def test_get_me_without_token(self, client, test_db):
        res = await client.get("/api/auth/me")
        assert res.status_code in (401, 403)

    async def test_get_me_invalid_token(self, client, test_db):
        res = await client.get("/api/auth/me", headers={"Authorization": "Bearer invalid_token_xxx"})
        assert res.status_code in (401, 403)

    async def test_idempotent_register(self, client, test_db, auth_token):
        """幂等注册：已存在用户再次注册应直接返回 token"""
        from backend.redis_client import cache
        await cache.set("email_code:test@example.com", "123456", 300)

        res = await client.post("/api/auth/register", json={
            "username": "testuser",  # 相同用户名
            "email": "test@example.com",  # 相同邮箱
            "email_code": "123456",
            "password": "Test123456",
        })
        # 已存在，应直接返回成功
        assert res.status_code == 200
        body = res.json()
        assert "token" in body["data"]
