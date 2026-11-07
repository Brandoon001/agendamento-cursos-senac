"""Modelo de curso pago ou gratuito."""

from __future__ import annotations

from app.extensions import db
from app.models.base import TimestampMixin
from app.models.enums import TipoCurso


def _valores_enum(enum_cls: type) -> list[str]:
    return [membro.value for membro in enum_cls]


class Curso(TimestampMixin, db.Model):
    """Curso ofertado pelo SENAC.

    Cursos pagos possuem um link externo individual de compra. Cursos gratuitos
    não possuem link externo e aceitam pré-inscrição interna.

    Cursos com inscrições não devem ser excluídos: o histórico precisa ser
    preservado. Nesses casos, o curso deve ser arquivado pela coluna ``ativo``.
    """

    __tablename__ = "cursos"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(180), unique=True, nullable=True, index=True)
    descricao = db.Column(db.Text, nullable=False, default="")
    tipo = db.Column(
        db.Enum(
            TipoCurso,
            native_enum=False,
            length=20,
            validate_strings=True,
            values_callable=_valores_enum,
        ),
        nullable=False,
        index=True,
    )
    link_externo = db.Column(db.String(500), nullable=True)
    valor = db.Column(db.Numeric(10, 2), nullable=True)
    carga_horaria = db.Column(db.Integer, nullable=True)
    data_inicio = db.Column(db.Date, nullable=True)
    data_fim = db.Column(db.Date, nullable=True)
    vagas = db.Column(db.Integer, nullable=True)
    imagem_url = db.Column(db.String(500), nullable=True)
    ativo = db.Column(db.Boolean, default=True, nullable=False, index=True)

    inscricoes = db.relationship(
        "Inscricao",
        back_populates="curso",
        passive_deletes=True,
    )

    __table_args__ = (
        db.CheckConstraint(
            "tipo IN ('pago', 'gratuito')",
            name="ck_cursos_tipo_valido",
        ),
        db.CheckConstraint(
            "(tipo = 'pago' AND link_externo IS NOT NULL) "
            "OR (tipo = 'gratuito' AND link_externo IS NULL)",
            name="ck_cursos_link_externo_por_tipo",
        ),
        db.CheckConstraint(
            "valor IS NULL OR valor >= 0",
            name="ck_cursos_valor_nao_negativo",
        ),
        db.CheckConstraint(
            "vagas IS NULL OR vagas >= 0",
            name="ck_cursos_vagas_nao_negativas",
        ),
        db.CheckConstraint(
            "carga_horaria IS NULL OR carga_horaria > 0",
            name="ck_cursos_carga_horaria_positiva",
        ),
        db.CheckConstraint(
            "data_fim IS NULL OR data_inicio IS NULL OR data_fim >= data_inicio",
            name="ck_cursos_periodo_valido",
        ),
        db.Index("ix_cursos_publicacao", "ativo", "tipo"),
    )

    @property
    def e_pago(self) -> bool:
        return self.tipo == TipoCurso.PAGO

    @property
    def e_gratuito(self) -> bool:
        return self.tipo == TipoCurso.GRATUITO

    @property
    def aceita_pre_inscricao(self) -> bool:
        """Indica se o curso pode receber uma pré-inscrição interna.

        Objetos novos ainda não passaram pelo flush, quando o valor padrão da
        coluna ``ativo`` é aplicado. Nesse caso, considera-se o curso ativo.
        """
        return self.ativo is not False and self.e_gratuito

    def __repr__(self) -> str:
        return f"<Curso {self.titulo!r} ({self.tipo.value})>"
