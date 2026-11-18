"""Modelo de curso gratuito do SENAC Sobral."""

from __future__ import annotations

from app.extensions import db
from app.models.base import TimestampMixin
from app.models.enums import StatusInscricao, TipoCurso


def _valores_enum(enum_cls: type) -> list[str]:
    return [membro.value for membro in enum_cls]


class Curso(TimestampMixin, db.Model):
    """Curso gratuito ofertado pelo SENAC Sobral.

    O catálogo público mostra apenas cursos ativos, gratuitos e da cidade
    configurada (``Sobral`` por padrão). Cursos com inscrições não devem ser
    excluídos: o histórico precisa ser preservado. Nesses casos, o curso deve
    ser arquivado pela coluna ``ativo``.
    """

    __tablename__ = "cursos"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(180), unique=True, nullable=True, index=True)
    cidade = db.Column(
        db.String(100),
        nullable=False,
        default="Sobral",
        server_default="Sobral",
        index=True,
    )
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
    turmas = db.relationship(
        "Turma",
        back_populates="curso",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Turma.nome",
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
        db.Index("ix_cursos_publicacao", "ativo", "tipo", "cidade"),
    )

    @property
    def situacao(self) -> str:
        """Situação textual do curso para exibição e integração."""
        return "ativo" if self.ativo else "inativo"

    @property
    def aceita_pre_inscricao(self) -> bool:
        """Indica se o curso pode receber uma pré-inscrição interna.

        Objetos novos ainda não passaram pelo flush, quando o valor padrão da
        coluna ``ativo`` é aplicado. Nesse caso, considera-se o curso ativo.
        """
        return self.ativo is not False

    @property
    def turmas_ativas(self) -> list:
        """Turmas ativas do curso, ordenadas pelo nome."""
        return [turma for turma in self.turmas if turma.ativo is not False]

    @property
    def vagas_ocupadas(self) -> int:
        """Inscrições ainda válidas (não canceladas) do curso."""
        return sum(
            1
            for inscricao in self.inscricoes
            if inscricao.status != StatusInscricao.CANCELADA
        )

    @property
    def vagas_disponiveis(self) -> int | None:
        """Vagas restantes do curso ou ``None`` quando não há limite definido.

        Quando o curso possui turmas, a disponibilidade é a soma das vagas
        restantes das turmas ativas. Caso contrário, usa-se o campo
        ``Curso.vagas`` como referência informativa.
        """
        turmas = self.turmas_ativas
        if turmas:
            if any(turma.vagas is None for turma in turmas):
                return None
            return sum(turma.vagas_disponiveis or 0 for turma in turmas)

        if self.vagas is None:
            return None
        return max(self.vagas - self.vagas_ocupadas, 0)

    @property
    def possui_vagas(self) -> bool:
        """Indica se o curso aceita novas inscrições por disponibilidade.

        Cursos inativos nunca possuem vagas para novas inscrições. Quando não
        há turmas ativas, o limite de referência do curso é usado.
        """
        if self.ativo is False:
            return False
        if not self.turmas_ativas:
            return self.vagas is None or self.vagas_disponiveis > 0
        return any(turma.disponivel for turma in self.turmas_ativas)

    def __repr__(self) -> str:
        return f"<Curso {self.titulo!r} ({self.cidade})>"
