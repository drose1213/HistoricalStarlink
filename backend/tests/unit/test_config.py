"""配置系统单元测试"""
import os
import pytest


@pytest.mark.unit
class TestConfigSystem:
    """验证配置优先级与默认值"""

    def setup_method(self):
        """每个测试前重置 settings"""
        from importlib import reload
        from backend import config as cfg_module
        reload(cfg_module)
        self.cfg = cfg_module.settings

    def test_settings_loaded(self):
        assert self.cfg.PROJECT_NAME
        assert self.cfg.SERVER_PORT > 0

    def test_db_type_fallback_sqlite(self):
        """未配置 MySQL 时自动回退到 SQLite"""
        self.cfg.MYSQL_HOST = "127.0.0.1"
        self.cfg.MYSQL_PORT = 33333  # 不存在端口
        self.cfg.DB_DRIVER = "auto"
        assert "sqlite" in self.cfg.DATABASE_URL.lower()

    def test_db_type_force_mysql(self):
        self.cfg.DB_DRIVER = "mysql"
        self.cfg.MYSQL_USER = "root"
        self.cfg.MYSQL_PASSWORD = "test"
        self.cfg.MYSQL_HOST = "127.0.0.1"
        assert "mysql" in self.cfg.DATABASE_URL.lower()

    def test_jwt_secret_key_always_set(self):
        """无论 DEBUG 与否，JWT 密钥必须存在"""
        assert self.cfg.JWT_SECRET_KEY, "JWT 密钥不能为空"

    def test_cors_origins_is_list(self):
        assert isinstance(self.cfg.CORS_ORIGINS, list)
        assert len(self.cfg.CORS_ORIGINS) > 0

    def test_smtp_defaults(self):
        assert self.cfg.SMTP_PORT > 0
        assert self.cfg.EMAIL_CODE_EXPIRE_SECONDS > 0

    def test_env_override_works(self):
        """环境变量应该能覆盖数据库配置"""
        os.environ["MYSQL_HOST"] = "192.168.1.100"
        os.environ["MYSQL_PORT"] = "3307"

        from importlib import reload
        from backend import config as cfg_module
        reload(cfg_module)
        cfg = cfg_module.settings

        assert cfg.MYSQL_HOST == "192.168.1.100"
        assert cfg.MYSQL_PORT == 3307

        del os.environ["MYSQL_HOST"]
        del os.environ["MYSQL_PORT"]
