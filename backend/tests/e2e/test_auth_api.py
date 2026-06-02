"""用户认证 API 黑盒测试"""
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
