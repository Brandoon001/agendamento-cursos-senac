"""Modelo de turma vinculada a um curso."""

from __future__ import annotations

from app.extensions import db
from app.models.base import TimestampMixin
from app.models.enums import StatusInscricao


class Turma(TimestampMixin, db.Model):
    """Turma de um curso, com horário próprio e controle de vagas.

    Um mesmo curso pode possuir várias turmas, cada uma com dias e horários
    diferentes. A turma com inscrições não deve ser excluída; nesse caso ela
    deve ser desativada para preservar o histórico.
    """

    __tablename__ = "turmas"

    id = db.Column(db.Integer, primary_key=True)
    curso_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "cursos.id",
            ondelete="CASCADE",
            name="fk_turmas_curso_id",
        ),
        nullable=False,
        index=True,
    )
    nome = db.Column(db.String(100), nullable=False)
    dias_semana = db.Column(db.String(120), nullable=True)
    hora_inicio = db.Column(db.Time(), nullable=True)
    hora_fim = db.Column(db.Time(), nullable=True)
    data_inicio = db.Column(db.Date, nullable=True)
    data_fim = db.Column(db.Date, nullable=True)
    vagas = db.Column(db.Integer, nullable=True)
    ativo = db.Column(db.Boolean, default=True, nullable=False, index=True)

    curso = db.relationship("Curso", back_populates="turmas")
    inscricoes = db.relationship(
        "Inscricao",
        back_populates="turma",
        passive_deletes=True,
    )

    __table_args__ = (
        db.CheckConstraint(
            "vagas IS NULL OR vagas >= 0",
            name="ck_turmas_vagas_nao_negativas",
        ),
        db.CheckConstraint(
            "hora_fim IS NULL OR hora_inicio IS NULL OR hora_fim > hora_inicio",
            name="ck_turmas_horario_valido",
        ),
        db.CheckConstraint(
            "data_fim IS NULL OR data_inicio IS NULL OR data_fim >= data_inicio",
            name="ck_turmas_periodo_valido",
        ),
        db.Index("ix_turmas_curso_ativo", "curso_id", "ativo"),
    )

    @property
    def situacao(self) -> str:
        """Situação textual da turma para exibição e integração."""
        return "ativa" if self.ativo else "inativa"

    @property
    def vagas_ocupadas(self) -> int:
        """Quantidade de inscrições que não foram canceladas."""
        return sum(
            1
            for inscricao in self.inscricoes
            if inscricao.status != StatusInscricao.CANCELADA
        )

    @property
    def vagas_disponiveis(self) -> int | None:
        """Vagas restantes ou ``None`` quando a turma não limita vagas."""
        if self.vagas is None:
            return None
        return max(self.vagas - self.vagas_ocupadas, 0)

    @property
    def tem_vagas(self) -> bool:
        """Indica se ainda é possível se inscrever na turma."""
        return self.vagas is None or self.vagas_disponiveis > 0

    @property
    def disponivel(self) -> bool:
        """Turma ativa, de curso ativo e com pelo menos uma vaga disponível."""
        curso_ativo = self.curso is None or self.curso.ativo is not False
        return self.ativo is not False and curso_ativo and self.tem_vagas

    @property
    def horario_formatado(self) -> str:
        if self.hora_inicio is None or self.hora_fim is None:
            return "Horário a definir"
        return (
            f"{self.hora_inicio.strftime('%H:%M')} às "
            f"{self.hora_fim.strftime('%H:%M')}"
        )

    def __repr__(self) -> str:
        return f"<Turma {self.nome!r} curso={self.curso_id}>"
