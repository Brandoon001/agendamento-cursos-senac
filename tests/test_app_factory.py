"""Testes da fundação e do registro dos módulos."""


def test_application_factory_usa_configuracao_de_teste(app):
    assert app.config["TESTING"] is True
    assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite:///:memory:"


def test_blueprints_essenciais_registrados(app):
    endpoints = {
        "main.index",
        "catalogo.listar",
        "catalogo.detalhe",
        "inscricoes.pre_inscricao",
        "inscricoes.confirmacao",
        "auth.login",
        "auth.logout",
        "admin.dashboard",
    }

    assert endpoints.issubset(app.view_functions)


def test_pagina_inicial_responde(client):
    resposta = client.get("/")

    assert resposta.status_code == 200
    assert b"SENAC Cursos" in resposta.data


def test_painel_administrativo_exige_autenticacao(client):
    resposta = client.get("/admin/")

    assert resposta.status_code == 302
    assert "/auth/login" in resposta.headers["Location"]
