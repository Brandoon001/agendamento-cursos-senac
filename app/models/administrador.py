"""Modelo do único administrador do sistema."""

from __future__ import annotations

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models.base import TimestampMixin


class Administrador(TimestampMixin, UserMixin, db.Model):
    """Representa o usuário administrativo autenticado no sistema.

    O sistema possui apenas um administrador. A regra de unicidade é aplicada
    pelo módulo administrativo no momento da criação do usuário.
    """

    __tablename__ = "administradores"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)

    inscricoes = db.relationship(
        "Inscricao",
        back_populates="administrador",
        foreign_keys="Inscricao.administrador_id",
        passive_deletes=True,
    )

    def definir_senha(self, senha: str) -> None:
        """Gera e armazena o hash da senha informada."""
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha: str) -> bool:
        """Compara uma senha em texto puro com o hash armazenado."""
        return check_password_hash(self.senha_hash, senha)

    @property
    def is_active(self) -> bool:
        """Integra o campo ``ativo`` com o Flask-Login.

        Objetos novos ainda não passaram pelo flush, quando o valor padrão da
        coluna é aplicado. Nesse caso, considera-se o administrador ativo.
        """
        return self.ativo is not False

    def __repr__(self) -> str:
        return f"<Administrador {self.email}>"
