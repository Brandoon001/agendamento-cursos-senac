"""Testes da fundação e do registro dos módulos."""

import pytest

from app import create_app
from app.config import ProductionConfig, get_config


def test_configuracao_desconhecida_e_rejeitada():
    with pytest.raises(ValueError, match="Configuração desconhecida"):
        get_config("produced")


def test_producao_exige_secret_key(monkeypatch):
    monkeypatch.setattr(
        ProductionConfig,
        "SECRET_KEY",
        "dev-apenas-troque-esta-chave",
    )

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app("production")


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
    assert b"SENAC Sobral" in resposta.data
    assert b"https://cursos.ce.senac.br/" in resposta.data
    assert b"cursos pagos" not in resposta.data.lower()


def test_catalogo_tem_um_unico_link_externo_para_o_portal(client):
    resposta = client.get("/cursos")

    assert resposta.status_code == 200
    assert resposta.data.count(b"https://cursos.ce.senac.br/") == 1
    assert b'target="_blank"' in resposta.data
    assert b'rel="noopener noreferrer"' in resposta.data
    assert b"Comprar" not in resposta.data


def test_painel_administrativo_exige_autenticacao(client):
    resposta = client.get("/admin/")

    assert resposta.status_code == 302
    assert "/auth/login" in resposta.headers["Location"]


def test_link_do_portal_nao_aparece_no_login(client):
    resposta = client.get("/auth/login")

    assert resposta.status_code == 200
    assert b"Outros cursos no SENAC" not in resposta.data
    assert b"https://cursos.ce.senac.br/" not in resposta.data


def test_link_do_portal_nao_aparece_no_painel_autenticado(client_autenticado):
    resposta = client_autenticado.get("/admin/")

    assert resposta.status_code == 200
    assert b"Outros cursos no SENAC" not in resposta.data
    assert b"https://cursos.ce.senac.br/" not in resposta.data


def test_link_de_login_nao_aparece_para_visitantes(client):
    for pagina in ("/", "/cursos"):
        resposta = client.get(pagina)

        assert resposta.status_code == 200
        assert b' href="/auth/login"' not in resposta.data
        assert b">Entrar<" not in resposta.data


def test_login_continua_disponivel_pela_url_direta(client):
    resposta = client.get("/auth/login")

    assert resposta.status_code == 200
