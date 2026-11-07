"""Elementos reutilizáveis pelos modelos da aplicação."""

from __future__ import annotations

from datetime import datetime, timezone

from app.extensions import db


def utcnow() -> datetime:
    """Retorna a data e hora atuais em UTC."""
    return datetime.now(timezone.utc)


class TimestampMixin:
    """Adiciona colunas de auditoria a um modelo."""

    criado_em = db.Column(
        db.DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )
    atualizado_em = db.Column(
        db.DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )
