"""Configurações centrais da aplicação.

As configurações são carregadas a partir de variáveis de ambiente, com valores
padrão seguros para desenvolvimento local. Nunca versione o arquivo ``.env``.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"

load_dotenv(BASE_DIR / ".env")


def _normalizar_database_url(url: str) -> str:
    """Ajusta URLs antigas de PostgreSQL para o formato aceito pelo SQLAlchemy."""
    if url.startswith("postgres://"):
        return "postgresql://" + url.removeprefix("postgres://")
    return url


class Config:
    """Configuração compartilhada por todos os ambientes."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-apenas-troque-esta-chave")
    SQLALCHEMY_DATABASE_URI = _normalizar_database_url(
        os.getenv(
            "DATABASE_URL",
            f"sqlite:///{INSTANCE_DIR / 'senac_cursos.db'}",
        )
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True

    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = int(os.getenv("WTF_CSRF_TIME_LIMIT", "3600"))

    MAX_CONTENT_LENGTH = 4 * 1024 * 1024


class DevelopmentConfig(Config):
    """Ambiente de desenvolvimento local."""

    DEBUG = True


class TestingConfig(Config):
    """Ambiente isolado usado pelos testes automatizados."""

    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "chave-exclusiva-de-testes"


class ProductionConfig(Config):
    """Ambiente de produção."""

    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


_CONFIGURACOES = {
    "development": DevelopmentConfig,
    "dev": DevelopmentConfig,
    "testing": TestingConfig,
    "test": TestingConfig,
    "production": ProductionConfig,
    "prod": ProductionConfig,
}


def get_config(nome: str | None = None) -> type[Config]:
    """Retorna a classe de configuração conforme nome ou variável de ambiente."""
    chave = (nome or os.getenv("FLASK_CONFIG") or "development").strip().lower()
    return _CONFIGURACOES.get(chave, DevelopmentConfig)
