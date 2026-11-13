"""Fixtures compartilhadas dos testes."""

import pytest

from app import create_app
from app.extensions import db, login_manager


@pytest.fixture()
def app():
    aplicacao = create_app("testing")
    login_manager.session_protection = None

    with aplicacao.app_context():
        db.create_all()
        yield aplicacao
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def administrador(app):
    from app.models import Administrador

    usuario = Administrador(
        nome="Administrador de Teste",
        email="admin@example.test",
    )
    usuario.definir_senha("senha-ficticia")
    db.session.add(usuario)
    db.session.commit()
    return usuario


@pytest.fixture()
def client_autenticado(client, administrador):
    with client.session_transaction() as sessao:
        sessao["_user_id"] = str(administrador.id)
        sessao["_fresh"] = True
    return client
