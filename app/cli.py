"""Comandos de terminal para operações de infraestrutura."""

from __future__ import annotations

import click
from flask import Flask
from flask.cli import with_appcontext

from app.extensions import db
from app.models import Administrador


@click.command("criar-admin")
@click.option("--nome", prompt="Nome do administrador")
@click.option("--email", prompt="E-mail do administrador")
@click.password_option("--senha", prompt="Senha", confirmation_prompt=True)
@with_appcontext
def criar_admin(nome: str, email: str, senha: str) -> None:
    """Cria o único administrador do sistema, se ainda não existir."""
    if db.session.scalar(db.select(Administrador).limit(1)) is not None:
        raise click.ClickException("Já existe um administrador cadastrado.")

    administrador = Administrador(nome=nome.strip(), email=email.strip().lower())
    administrador.definir_senha(senha)

    db.session.add(administrador)
    db.session.commit()

    click.echo(f"Administrador {administrador.email} criado com sucesso.")


def registrar_comandos(app: Flask) -> None:
    """Adiciona os comandos CLI à aplicação."""
    app.cli.add_command(criar_admin)
