"""Comandos de terminal para operações de infraestrutura."""

from __future__ import annotations

import click
from flask import Flask
from flask.cli import with_appcontext

from app.extensions import db
from app.models import Administrador, Curso
from app.services.curso_service import CursoService


CURSOS_DEMO = (
    {
        "titulo": "Informática Básica",
        "descricao": "Noções de computador, arquivos, internet e ferramentas digitais.",
        "cidade": "Sobral",
        "carga_horaria": 40,
        "vagas": 30,
        "data_inicio": "2026-11-30",
        "data_fim": "2026-12-18",
        "turmas": (
            {
                "nome": "Turma Manhã",
                "dias_semana": "Segunda a sexta",
                "hora_inicio": "08:00",
                "hora_fim": "12:00",
                "vagas": 15,
                "ativo": True,
            },
            {
                "nome": "Turma Noite",
                "dias_semana": "Terça e quinta",
                "hora_inicio": "19:00",
                "hora_fim": "22:00",
                "vagas": 15,
                "ativo": True,
            },
        ),
    },
    {
        "titulo": "Comunicação e Expressão",
        "descricao": "Leitura, escrita e apresentação de ideias no cotidiano profissional.",
        "cidade": "Sobral",
        "carga_horaria": 30,
        "vagas": 20,
        "data_inicio": "2026-12-01",
        "data_fim": "2026-12-15",
        "turmas": (
            {
                "nome": "Turma Única",
                "dias_semana": "Segunda e quarta",
                "hora_inicio": "18:00",
                "hora_fim": "21:00",
                "vagas": 20,
                "ativo": True,
            },
        ),
    },
    {
        "titulo": "Primeiros Socorros",
        "descricao": "Procedimentos básicos de atendimento e prevenção de acidentes.",
        "cidade": "Sobral",
        "carga_horaria": 16,
        "vagas": 25,
        "data_inicio": "2026-12-05",
        "data_fim": "2026-12-06",
        "turmas": (
            {
                "nome": "Turma Sábado",
                "dias_semana": "Sábado",
                "hora_inicio": "09:00",
                "hora_fim": "17:00",
                "vagas": 25,
                "ativo": True,
            },
        ),
    },
)


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


@click.command("seed-demo")
@click.option(
    "--senha",
    default="senac123",
    show_default=True,
    help="Senha do administrador de demonstração.",
)
@with_appcontext
def seed_demo(senha: str) -> None:
    """Popula o banco com cursos e turmas fictícios para demonstração."""
    if db.session.scalar(db.select(Administrador).limit(1)) is None:
        administrador = Administrador(
            nome="Administrador de Demonstração",
            email="admin@senac.br",
        )
        administrador.definir_senha(senha)
        db.session.add(administrador)
        db.session.commit()
        click.echo("Administrador de demonstração criado: admin@senac.br")

    servico = CursoService()
    criados = 0
    for dados in CURSOS_DEMO:
        titulo = dados["titulo"]
        if db.session.scalar(
            db.select(Curso).where(Curso.titulo == titulo)
        ) is not None:
            continue
        curso = servico.criar_curso(
            {chave: valor for chave, valor in dados.items() if chave != "turmas"}
        )
        for turma in dados["turmas"]:
            servico.criar_turma(curso.id, turma)
        criados += 1

    click.echo(f"{criados} curso(s) de demonstração criado(s).")
    click.echo("Use `flask seed-demo --senha ...` em ambiente local apenas.")


def registrar_comandos(app: Flask) -> None:
    """Adiciona os comandos CLI à aplicação."""
    app.cli.add_command(criar_admin)
    app.cli.add_command(seed_demo)
