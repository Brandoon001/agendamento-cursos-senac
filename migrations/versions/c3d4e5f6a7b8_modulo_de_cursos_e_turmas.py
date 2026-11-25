"""adiciona turmas e vinculo da inscricao com a turma

Revision ID: c3d4e5f6a7b8
Revises: b7c1d2e3f4a5
Create Date: 2026-11-12 00:00:00.000000

Alterações:
- cria a tabela ``turmas`` com horários, período e vagas próprias;
- permite que um curso tenha várias turmas;
- adiciona ``inscricoes.turma_id`` (opcional) para o controle de vagas por
  turma, preservando inscrições quando uma turma é removida.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c3d4e5f6a7b8"
down_revision = "b7c1d2e3f4a5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "turmas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("curso_id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("dias_semana", sa.String(length=120), nullable=True),
        sa.Column("hora_inicio", sa.Time(), nullable=True),
        sa.Column("hora_fim", sa.Time(), nullable=True),
        sa.Column("data_inicio", sa.Date(), nullable=True),
        sa.Column("data_fim", sa.Date(), nullable=True),
        sa.Column("vagas", sa.Integer(), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "vagas IS NULL OR vagas >= 0",
            name="ck_turmas_vagas_nao_negativas",
        ),
        sa.CheckConstraint(
            "hora_fim IS NULL OR hora_inicio IS NULL "
            "OR hora_fim > hora_inicio",
            name="ck_turmas_horario_valido",
        ),
        sa.CheckConstraint(
            "data_fim IS NULL OR data_inicio IS NULL "
            "OR data_fim >= data_inicio",
            name="ck_turmas_periodo_valido",
        ),
        sa.ForeignKeyConstraint(
            ["curso_id"],
            ["cursos.id"],
            name="fk_turmas_curso_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("turmas", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_turmas_curso_id"),
            ["curso_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_turmas_ativo"),
            ["ativo"],
            unique=False,
        )
        batch_op.create_index(
            "ix_turmas_curso_ativo",
            ["curso_id", "ativo"],
            unique=False,
        )

    with op.batch_alter_table("inscricoes", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("turma_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_inscricoes_turma_id",
            "turmas",
            ["turma_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index(
            batch_op.f("ix_inscricoes_turma_id"),
            ["turma_id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("inscricoes", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_inscricoes_turma_id"))
        batch_op.drop_constraint(
            "fk_inscricoes_turma_id",
            type_="foreignkey",
        )
        batch_op.drop_column("turma_id")

    with op.batch_alter_table("turmas", schema=None) as batch_op:
        batch_op.drop_index("ix_turmas_curso_ativo")
        batch_op.drop_index(batch_op.f("ix_turmas_ativo"))
        batch_op.drop_index(batch_op.f("ix_turmas_curso_id"))

    op.drop_table("turmas")
