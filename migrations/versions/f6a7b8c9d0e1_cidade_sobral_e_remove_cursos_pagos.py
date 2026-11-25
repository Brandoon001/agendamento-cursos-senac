"""adiciona cidade aos cursos e remove cursos pagos

Revision ID: f6a7b8c9d0e1
Revises: c3d4e5f6a7b8
Create Date: 2026-11-17 00:00:00.000000

Alterações:
- exclui cursos pagos e o histórico vinculado a eles;
- adiciona ``cursos.cidade`` com padrão ``Sobral``;
- cria índice para o filtro por cidade.

Os cursos pagos excluídos não podem ser restaurados no downgrade.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f6a7b8c9d0e1"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "DELETE FROM inscricoes WHERE curso_id IN "
        "(SELECT id FROM cursos WHERE tipo = 'pago')"
    )
    op.execute(
        "DELETE FROM turmas WHERE curso_id IN "
        "(SELECT id FROM cursos WHERE tipo = 'pago')"
    )
    op.execute("DELETE FROM cursos WHERE tipo = 'pago'")

    op.add_column(
        "cursos",
        sa.Column(
            "cidade",
            sa.String(length=100),
            nullable=False,
            server_default="Sobral",
        ),
    )
    op.create_index("ix_cursos_cidade", "cursos", ["cidade"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_cursos_cidade", table_name="cursos")
    op.drop_column("cursos", "cidade")
