"""Configuração do app. Segredos vêm só de variáveis de ambiente."""

import os

from dotenv import load_dotenv

load_dotenv()


def normalize_db_url(url: str | None) -> str | None:
    """Usa o driver PyMySQL e garante utf8mb4 na conexão.

    Aceita URLs no formato `mysql://...` (como o Railway fornece).
    """
    if not url:
        return url
    if url.startswith("mysql://"):
        url = "mysql+pymysql://" + url.removeprefix("mysql://")
    if "charset=" not in url:
        url += ("&" if "?" in url else "?") + "charset=utf8mb4"
    return url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = normalize_db_url(os.environ.get("DATABASE_URL"))
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}
    SQLALCHEMY_ECHO = False  # nunca logar SQL: os dados são de menores
    WTF_CSRF_ENABLED = True
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024


class DevelopmentConfig(Config):
    DEBUG = True
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-insecure-key")
    SQLALCHEMY_DATABASE_URI = normalize_db_url(
        os.environ.get("DATABASE_URL", "mysql+pymysql://boletim:boletim@127.0.0.1:3306/boletim")
    )


class TestingConfig(Config):
    TESTING = True
    SECRET_KEY = "test-only-key"
    SQLALCHEMY_DATABASE_URI = normalize_db_url(
        os.environ.get(
            "TEST_DATABASE_URL",
            "mysql+pymysql://boletim:boletim@127.0.0.1:3307/boletim_test",
        )
    )


class ProductionConfig(Config):
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"


CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
