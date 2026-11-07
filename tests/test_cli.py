"""Testes do comando de criação do administrador."""

from app.extensions import db
from app.models import Administrador


def test_criar_admin_persiste_unico_administrador(app):
    runner = app.test_cli_runner()

    resultado = runner.invoke(
        args=[
            "criar-admin",
            "--nome",
            "Administrador de Teste",
            "--email",
            "admin@example.test",
            "--senha",
            "senha-ficticia",
        ]
    )

    assert resultado.exit_code == 0
    assert db.session.query(Administrador).count() == 1


def test_criar_admin_recusa_segundo_registro(app):
    runner = app.test_cli_runner()
    argumentos = [
        "criar-admin",
        "--nome",
        "Administrador de Teste",
        "--email",
        "admin@example.test",
        "--senha",
        "senha-ficticia",
    ]

    runner.invoke(args=argumentos)
    resultado = runner.invoke(args=argumentos)

    assert resultado.exit_code != 0
    assert "Já existe um administrador cadastrado" in resultado.output
    assert db.session.query(Administrador).count() == 1
