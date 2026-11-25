"""Testes de autenticação e logout do administrador."""

from __future__ import annotations

from app.extensions import db
from app.services.autenticacao_service import AutenticacaoService


def test_login_com_credenciais_validas(client, administrador):
    resposta = client.post(
        "/auth/login",
        data={"email": administrador.email, "senha": "senha-ficticia"},
        follow_redirects=True,
    )

    assert resposta.status_code == 200
    assert b"Painel administrativo" in resposta.data
    with client.session_transaction() as sessao:
        assert sessao["_user_id"] == str(administrador.id)


def test_login_com_senha_invalida_nao_autentica(client, administrador):
    resposta = client.post(
        "/auth/login",
        data={"email": administrador.email, "senha": "senha-errada"},
    )

    assert resposta.status_code == 200
    assert b"E-mail ou senha inv\xc3\xa1lidos" in resposta.data
    with client.session_transaction() as sessao:
        assert "_user_id" not in sessao


def test_login_aceita_email_com_espacos_e_maiusculas(client, administrador):
    resposta = client.post(
        "/auth/login",
        data={"email": f"  {administrador.email.upper()}  ", "senha": "senha-ficticia"},
    )

    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/admin/")


def test_login_redireciona_para_destino_interno(client, administrador):
    client.get("/admin/cursos")
    resposta = client.post(
        "/auth/login?next=/admin/cursos",
        data={"email": administrador.email, "senha": "senha-ficticia"},
    )

    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/admin/cursos")


def test_login_rejeita_destino_externo(client, administrador):
    resposta = client.post(
        "/auth/login?next=https://site-externo.example/test",
        data={"email": administrador.email, "senha": "senha-ficticia"},
    )

    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/admin/")


def test_logout_encerra_sessao(client_autenticado):
    resposta = client_autenticado.post("/auth/logout")

    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/")
    assert client_autenticado.get("/admin/").status_code == 302


def test_servico_nao_autentica_administrador_inativo(administrador):
    administrador.ativo = False
    db.session.commit()

    assert (
        AutenticacaoService().autenticar(
            administrador.email,
            "senha-ficticia",
        )
        is None
    )
