"""preserva historico de inscricoes e revisa status

Revision ID: b7c1d2e3f4a5
Revises: e20f62e9afcd
Create Date: 2026-11-07 16:00:00.000000

Alterações:
- impede a exclusão de cursos que possuem inscrições (FK ON DELETE RESTRICT);
- preserva o histórico de inscrições;
- atualiza os status para recebida, em_analise, contatada, finalizada e
  cancelada;
- torna CPF e e-mail opcionais, deixando a obrigatoriedade para a validação
  do módulo de inscrições.

Mapeamento dos status antigos:
- pendente -> recebida;
- lista_espera -> em_analise;
- confirmada -> finalizada;
- cancelada -> cancelada.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b7c1d2e3f4a5"
down_revision = "e20f62e9afcd"
branch_labels = None
depends_on = None


STATUS_ANTIGOS = sa.Enum(
    "pendente",
    "confirmada",
    "cancelada",
    "lista_espera",
    name="statusinscricao",
    native_enum=False,
    length=20,
)
STATUS_NOVOS = sa.Enum(
    "recebida",
    "em_analise",
    "contatada",
    "finalizada",
    "cancelada",
    name="statusinscricao",
    native_enum=False,
    length=20,
)


def _nome_fk_atual(coluna: str) -> str | None:
    """Obtém o nome real da FK, inclusive em bancos que renomeiam constraints."""
    inspetor = sa.inspect(op.get_bind())
    for fk in inspetor.get_foreign_keys("inscricoes"):
        if fk.get("constrained_columns") == [coluna]:
            return fk.get("name")
    return None


def _batch_inscricoes(tabela_referencia: sa.Table):
    """No SQLite o batch recria a tabela; nos demais bancos usa ALTER direto."""
    if op.get_bind().dialect.name == "sqlite":
        return op.batch_alter_table(
            "inscricoes",
            copy_from=tabela_referencia,
            recreate="always",
        )
    return op.batch_alter_table("inscricoes")


def _tabela_inscricoes(
    *,
    status_type: sa.Enum,
    fk_curso_ondelete: str,
    cpf_nullable: bool,
    email_nullable: bool,
) -> sa.Table:
    metadata = sa.MetaData()
    return sa.Table(
        "inscricoes",
        metadata,
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("curso_id", sa.Integer(), nullable=False),
        sa.Column("administrador_id", sa.Integer(), nullable=True),
        sa.Column("nome_completo", sa.String(length=150), nullable=False),
        sa.Column("cpf", sa.String(length=14), nullable=cpf_nullable),
        sa.Column("email", sa.String(length=255), nullable=email_nullable),
        sa.Column("telefone", sa.String(length=20), nullable=True),
        sa.Column("data_nascimento", sa.Date(), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
        sa.Column("status", status_type, nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["administrador_id"],
            ["administradores.id"],
            name="fk_inscricoes_administrador_id",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["curso_id"],
            ["cursos.id"],
            name="fk_inscricoes_curso_id",
            ondelete=fk_curso_ondelete,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "curso_id",
            "cpf",
            name="uq_inscricoes_curso_cpf",
        ),
        sa.Index("ix_inscricoes_administrador_id", "administrador_id"),
        sa.Index("ix_inscricoes_curso_id", "curso_id"),
        sa.Index("ix_inscricoes_curso_status", "curso_id", "status"),
        sa.Index("ix_inscricoes_email", "email"),
        sa.Index("ix_inscricoes_status", "status"),
    )


def upgrade() -> None:
    op.execute(
        """
        UPDATE inscricoes
        SET status = CASE status
            WHEN 'pendente' THEN 'recebida'
            WHEN 'confirmada' THEN 'finalizada'
            WHEN 'lista_espera' THEN 'em_analise'
            WHEN 'cancelada' THEN 'cancelada'
            ELSE status
        END
        """
    )

    tabela_anterior = _tabela_inscricoes(
        status_type=STATUS_ANTIGOS,
        fk_curso_ondelete="CASCADE",
        cpf_nullable=False,
        email_nullable=False,
    )

    nome_fk_curso = _nome_fk_atual("curso_id") or "fk_inscricoes_curso_id"
    nome_fk_admin = (
        _nome_fk_atual("administrador_id") or "fk_inscricoes_administrador_id"
    )

    with _batch_inscricoes(tabela_anterior) as batch_op:
        batch_op.drop_constraint(nome_fk_curso, type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_inscricoes_curso_id",
            "cursos",
            ["curso_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch_op.drop_constraint(
            nome_fk_admin,
            type_="foreignkey",
        )
        batch_op.create_foreign_key(
            "fk_inscricoes_administrador_id",
            "administradores",
            ["administrador_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.alter_column(
            "cpf",
            existing_type=sa.String(length=14),
            nullable=True,
        )
        batch_op.alter_column(
            "email",
            existing_type=sa.String(length=255),
            nullable=True,
        )
        batch_op.alter_column(
            "status",
            existing_type=STATUS_ANTIGOS,
            type_=STATUS_NOVOS,
            existing_nullable=False,
        )


def downgrade() -> None:
    # A reversão precisa preencher CPF/e-mail para voltar ao schema antigo.
    # Os valores abaixo são apenas marcadores técnicos, não dados reais.
    op.execute(
        "UPDATE inscricoes SET cpf = 'SEM-CPF-' || id WHERE cpf IS NULL"
    )
    op.execute(
        "UPDATE inscricoes "
        "SET email = 'sem-email-' || id || '@example.invalid' "
        "WHERE email IS NULL"
    )
    op.execute(
        """
        UPDATE inscricoes
        SET status = CASE status
            WHEN 'recebida' THEN 'pendente'
            WHEN 'em_analise' THEN 'lista_espera'
            WHEN 'contatada' THEN 'lista_espera'
            WHEN 'finalizada' THEN 'confirmada'
            WHEN 'cancelada' THEN 'cancelada'
            ELSE status
        END
        """
    )

    tabela_atual = _tabela_inscricoes(
        status_type=STATUS_NOVOS,
        fk_curso_ondelete="RESTRICT",
        cpf_nullable=True,
        email_nullable=True,
    )

    nome_fk_curso = _nome_fk_atual("curso_id") or "fk_inscricoes_curso_id"
    nome_fk_admin = (
        _nome_fk_atual("administrador_id") or "fk_inscricoes_administrador_id"
    )

    with _batch_inscricoes(tabela_atual) as batch_op:
        batch_op.drop_constraint(nome_fk_curso, type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_inscricoes_curso_id",
            "cursos",
            ["curso_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.drop_constraint(
            nome_fk_admin,
            type_="foreignkey",
        )
        batch_op.create_foreign_key(
            "fk_inscricoes_administrador_id",
            "administradores",
            ["administrador_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.alter_column(
            "cpf",
            existing_type=sa.String(length=14),
            nullable=False,
        )
        batch_op.alter_column(
            "email",
            existing_type=sa.String(length=255),
            nullable=False,
        )
        batch_op.alter_column(
            "status",
            existing_type=STATUS_NOVOS,
            type_=STATUS_ANTIGOS,
            existing_nullable=False,
        )
