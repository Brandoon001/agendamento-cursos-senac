"""Testes do fluxo público de pré-inscrição."""

from datetime import date, timedelta

from app.extensions import db
from app.models import Curso, Inscricao, StatusInscricao, TipoCurso


def criar_curso(tipo=TipoCurso.GRATUITO, ativo=True):
    curso = Curso(
        titulo="Excel Básico",
        descricao="Curso fictício para testes.",
        tipo=tipo,
        link_externo=(
            "https://exemplo.test/compra"
            if tipo is TipoCurso.PAGO
            else None
        ),
        ativo=ativo,
    )

    db.session.add(curso)
    db.session.commit()

    return curso


def dados_validos(**alteracoes):
    dados = {
        "nome_completo": "Pessoa Teste",
        "cpf": "000.000.000-00",
        "email": "pessoa@example.com",
        "telefone": "(88) 99999-9999",
        "data_nascimento": (date.today() - timedelta(days=365 * 20)).isoformat(),
    }
    dados.update(alteracoes)
    return dados


def test_pre_inscricao_registra_dados_e_status_recebida(client, app):
    with app.app_context():
        curso = criar_curso()
        curso_id = curso.id

    resposta = client.post(
        f"/inscricoes/{curso_id}/pre-inscricao",
        data=dados_validos(),
        follow_redirects=True,
    )

    assert resposta.status_code == 200

    with app.app_context():
        inscricao = Inscricao.query.one()

        assert inscricao.nome_completo == "Pessoa Teste"
        assert inscricao.cpf == "00000000000"
        assert inscricao.email == "pessoa@example.com"       
        assert inscricao.telefone == "88999999999"
        assert inscricao.status is StatusInscricao.RECEBIDA


def test_cpf_duplicado_no_mesmo_curso_nao_cria_segunda_inscricao(
    client,
    app,
):
    with app.app_context():
        curso = criar_curso()
        curso_id = curso.id

        from app.services.inscricao_service import inscricao_service

        inscricao_service.criar_pre_inscricao(
            curso_id,
            {
                "nome_completo": "Pessoa Um",
                "cpf": "00000000000",
                "email": "um@example.test",
                "telefone": "88999999999",
                "data_nascimento": date(2000, 1, 1),
            },
        )

    resposta = client.post(
        f"/inscricoes/{curso_id}/pre-inscricao",
        data=dados_validos(),
    )

    assert resposta.status_code == 200
    assert b"CPF" in resposta.data

    with app.app_context():
        assert Inscricao.query.count() == 1


def test_curso_pago_nao_recebe_pre_inscricao(client, app):
    with app.app_context():
        curso = criar_curso(tipo=TipoCurso.PAGO)
        curso_id = curso.id

    resposta = client.get(
        f"/inscricoes/{curso_id}/pre-inscricao"
    )

    assert resposta.status_code == 302


def test_curso_arquivado_nao_recebe_pre_inscricao(client, app):
    with app.app_context():
        curso = criar_curso(ativo=False)
        curso_id = curso.id

    resposta = client.get(
        f"/inscricoes/{curso_id}/pre-inscricao"
    )

    assert resposta.status_code == 302


def test_curso_inexistente_retorna_404(client):
    resposta = client.get(
        "/inscricoes/99999/pre-inscricao"
    )

    assert resposta.status_code == 404


def test_data_de_nascimento_futura_e_rejeitada(client, app):
    with app.app_context():
        curso = criar_curso()
        curso_id = curso.id

    resposta = client.post(
        f"/inscricoes/{curso_id}/pre-inscricao",
        data=dados_validos(
            data_nascimento=(
                date.today() + timedelta(days=1)
            ).isoformat()
        ),
    )

    assert resposta.status_code == 200

    with app.app_context():
        assert Inscricao.query.count() == 0


def test_campos_obrigatorios_sao_validados(client, app):
    with app.app_context():
        curso = criar_curso()
        curso_id = curso.id

    resposta = client.post(
        f"/inscricoes/{curso_id}/pre-inscricao",
        data={"nome_completo": "Pessoa Teste"},
    )

    assert resposta.status_code == 200

    with app.app_context():
        assert Inscricao.query.count() == 0