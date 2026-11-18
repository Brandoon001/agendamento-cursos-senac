"""torna o CPF único em todas as inscrições

Revision ID: a2b3c4d5e6f7
Revises: f6a7b8c9d0e1
Create Date: 2026-11-17 00:00:00.000000

Alterações:
- normaliza CPFs antigos para o formato 000.000.000-00;
- mantém apenas a inscrição mais antiga de cada CPF, limpando o CPF das
  demais para preservar o histórico sem violar a unicidade;
- substitui a constraint por curso pela constraint global de CPF.
"""
import re

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a2b3c4d5e6f7"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def _digitos(valor: object) -> str:
    return re.sub(r"\D", "", str(valor or ""))


def _mascarar(digitos: str) -> str:
    return f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}"


def upgrade() -> None:
    conexao = op.get_bind()
    linhas = conexao.execute(
        sa.text("SELECT id, cpf FROM inscricoes WHERE cpf IS NOT NULL ORDER BY id")
    ).fetchall()

    vistos: set[str] = set()
    atualizacoes: list[tuple[str | None, int]] = []
    for id_inscricao, cpf in linhas:
        digitos = _digitos(cpf)
        if len(digitos) != 11 or digitos in vistos:
            atualizacoes.append((None, id_inscricao))
            continue
        vistos.add(digitos)
        atualizacoes.append((_mascarar(digitos), id_inscricao))

    for cpf, id_inscricao in atualizacoes:
        conexao.execute(
            sa.text("UPDATE inscricoes SET cpf = :cpf WHERE id = :id"),
            {"cpf": cpf, "id": id_inscricao},
        )

    with op.batch_alter_table("inscricoes") as batch_op:
        batch_op.drop_constraint("uq_inscricoes_curso_cpf", type_="unique")
        batch_op.create_unique_constraint("uq_inscricoes_cpf", ["cpf"])


def downgrade() -> None:
    with op.batch_alter_table("inscricoes") as batch_op:
        batch_op.drop_constraint("uq_inscricoes_cpf", type_="unique")
        batch_op.create_unique_constraint(
            "uq_inscricoes_curso_cpf",
            ["curso_id", "cpf"],
        )
