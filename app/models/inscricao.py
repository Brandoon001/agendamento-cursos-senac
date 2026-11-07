"""Modelo de pré-inscrição em curso gratuito."""

from __future__ import annotations

from app.extensions import db
from app.models.base import TimestampMixin
from app.models.enums import StatusInscricao


def _valores_enum(enum_cls: type) -> list[str]:
    return [membro.value for membro in enum_cls]


class Inscricao(TimestampMixin, db.Model):
    """Pré-inscrição de um interessado em um curso gratuito.

    A validação de que o curso é gratuito e está ativo deve ser feita pela
    camada de serviço do módulo de inscrições antes da persistência.

    CPF, e-mail e telefone são opcionais nesta fundação. A obrigatoriedade
    desses campos será definida posteriormente pelo módulo de inscrições.
    """

    __tablename__ = "inscricoes"

    id = db.Column(db.Integer, primary_key=True)
    curso_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "cursos.id",
            ondelete="RESTRICT",
            name="fk_inscricoes_curso_id",
        ),
        nullable=False,
        index=True,
    )
    administrador_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "administradores.id",
            ondelete="SET NULL",
            name="fk_inscricoes_administrador_id",
        ),
        nullable=True,
        index=True,
    )

    nome_completo = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(14), nullable=True)
    email = db.Column(db.String(255), nullable=True, index=True)
    telefone = db.Column(db.String(20), nullable=True)
    data_nascimento = db.Column(db.Date, nullable=True)
    observacoes = db.Column(db.Text, nullable=True)

    status = db.Column(
        db.Enum(
            StatusInscricao,
            native_enum=False,
            length=20,
            validate_strings=True,
            values_callable=_valores_enum,
        ),
        default=StatusInscricao.RECEBIDA,
        nullable=False,
        index=True,
    )

    curso = db.relationship("Curso", back_populates="inscricoes")
    administrador = db.relationship(
        "Administrador",
        back_populates="inscricoes",
        foreign_keys=[administrador_id],
    )

    __table_args__ = (
        db.UniqueConstraint(
            "curso_id",
            "cpf",
            name="uq_inscricoes_curso_cpf",
        ),
        db.Index("ix_inscricoes_curso_status", "curso_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Inscricao {self.nome_completo!r} curso={self.curso_id}>"
