"""Testes de pré-inscrição, painel administrativo e exportação."""

from __future__ import annotations

from io import BytesIO

import pytest
from openpyxl import load_workbook

from app.extensions import db
from app.forms.inscricao import cpf_e_valido, formatar_cpf
from app.models import Inscricao, StatusInscricao
from app.services.curso_service import CursoService
from app.services.inscricao_service import InscricaoService


def criar_curso_gratuito(vagas: int = 10):
    return CursoService().criar_curso(
        {
            "titulo": "Curso Gratuito Fictício",
            "descricao": "Conteúdo fictício usado apenas em testes.",
            "cidade": "Sobral",
            "vagas": vagas,
            "ativo": True,
        }
    )


def dados_validos(cpf: str = "529.982.247-25") -> dict:
    return {
        "nome_completo": "Aluno Fictício",
        "cpf": cpf,
        "email": "aluno@example.com",
        "telefone": "(11) 98888-7777",
        "aceite": "y",
    }


def test_validacao_e_formatacao_de_cpf():
    assert cpf_e_valido("529.982.247-25") is True
    assert cpf_e_valido("52998224725") is True
    assert cpf_e_valido("123.456.789-00") is False
    assert formatar_cpf("52998224725") == "529.982.247-25"


def test_servico_cria_inscricao_recebida(app):
    curso = criar_curso_gratuito()

    inscricao = InscricaoService().criar_pre_inscricao(
        curso.id,
        {
            "nome_completo": "Aluno Fictício",
            "cpf": "529.982.247-25",
            "email": "aluno@example.com",
        },
    )

    assert inscricao.id is not None
    assert inscricao.status is StatusInscricao.RECEBIDA
    assert inscricao.curso is curso
    assert inscricao.protocolo.startswith("INS-")
    assert inscricao.situacao == "Recebida"


def test_servico_vincula_inscricao_a_turma(app):
    curso = criar_curso_gratuito()
    turma = CursoService().criar_turma(
        curso.id,
        {"nome": "Turma A", "vagas": 3, "ativo": True},
    )

    inscricao = InscricaoService().criar_pre_inscricao(
        curso.id,
        {"nome_completo": "Aluno Fictício", "cpf": "529.982.247-25"},
        turma_id=turma.id,
    )

    assert inscricao.turma is turma
    assert turma.vagas_disponiveis == 2


def test_servico_rejeita_curso_inativo(app):
    curso = criar_curso_gratuito()
    curso.ativo = False
    db.session.commit()

    with pytest.raises(ValueError, match="não aceita"):
        InscricaoService().criar_pre_inscricao(
            curso.id,
            {"nome_completo": "Aluno Fictício", "cpf": "529.982.247-25"},
        )


def test_servico_impede_cpf_duplicado_no_mesmo_curso(app):
    curso = criar_curso_gratuito()
    servico = InscricaoService()
    servico.criar_pre_inscricao(
        curso.id,
        {"nome_completo": "Primeiro Aluno", "cpf": "529.982.247-25"},
    )

    with pytest.raises(ValueError, match="CPF"):
        servico.criar_pre_inscricao(
            curso.id,
            {"nome_completo": "Segundo Aluno", "cpf": "529.982.247-25"},
        )


def test_servico_bloqueia_turma_sem_vagas(app):
    curso = criar_curso_gratuito()
    turma = CursoService().criar_turma(
        curso.id,
        {"nome": "Turma Única", "vagas": 1, "ativo": True},
    )
    servico = InscricaoService()
    servico.criar_pre_inscricao(
        curso.id,
        {"nome_completo": "Primeiro Aluno", "cpf": "529.982.247-25"},
        turma_id=turma.id,
    )

    with pytest.raises(ValueError, match="vagas"):
        servico.criar_pre_inscricao(
            curso.id,
            {"nome_completo": "Segundo Aluno", "cpf": "168.995.350-09"},
            turma_id=turma.id,
        )


def test_formulario_publico_registra_e_exibe_confirmacao(client, app):
    curso = criar_curso_gratuito()
    turma = CursoService().criar_turma(
        curso.id,
        {"nome": "Turma A", "vagas": 3, "ativo": True},
    )

    resposta = client.post(
        f"/inscricoes/{curso.id}/pre-inscricao?turma_id={turma.id}",
        data=dados_validos(),
    )
    assert resposta.status_code == 302

    inscricao = db.session.scalar(db.select(Inscricao))
    assert inscricao is not None
    assert inscricao.turma_id == turma.id
    assert resposta.headers["Location"].endswith(
        f"/inscricoes/{inscricao.id}/confirmacao"
    )

    confirmacao = client.get(resposta.headers["Location"])
    assert confirmacao.status_code == 200
    assert inscricao.protocolo.encode() in confirmacao.data
    assert b"Aluno Fict\xc3\xadcio" in confirmacao.data
    assert b"Turma A" in confirmacao.data


def test_formulario_rejeita_cpf_invalido(client):
    curso = criar_curso_gratuito()

    resposta = client.post(
        f"/inscricoes/{curso.id}/pre-inscricao",
        data=dados_validos(cpf="000.000.000-00"),
    )

    assert resposta.status_code == 200
    assert b"CPF v\xc3\xa1lido" in resposta.data
    assert db.session.scalar(db.select(db.func.count()).select_from(Inscricao)) == 0


def test_confirmacao_nao_expõe_dados_de_outras_sessoes(app):
    curso = criar_curso_gratuito()
    inscricao = InscricaoService().criar_pre_inscricao(
        curso.id,
        {"nome_completo": "Aluno Fictício", "cpf": "529.982.247-25"},
    )

    outro_cliente = app.test_client()
    resposta = outro_cliente.get(
        f"/inscricoes/{inscricao.id}/confirmacao"
    )

    assert resposta.status_code == 404


def test_painel_admin_exige_autenticacao(client):
    assert client.get("/admin/inscricoes").status_code == 302
    assert client.get("/admin/inscricoes/exportar").status_code == 302


def test_painel_admin_lista_filtra_e_atualiza_status(client_autenticado, administrador):
    curso = criar_curso_gratuito()
    inscricao = InscricaoService().criar_pre_inscricao(
        curso.id,
        {"nome_completo": "Aluno Fictício", "cpf": "529.982.247-25"},
    )

    resposta = client_autenticado.get("/admin/inscricoes")
    assert resposta.status_code == 200
    assert b"Aluno Fict\xc3\xadcio" in resposta.data
    assert inscricao.protocolo.encode() in resposta.data

    resposta = client_autenticado.post(
        f"/admin/inscricoes/{inscricao.id}/status",
        data={"status": "finalizada"},
    )
    assert resposta.status_code == 302

    db.session.refresh(inscricao)
    assert inscricao.status is StatusInscricao.FINALIZADA
    assert inscricao.administrador_id == administrador.id

    filtrada = client_autenticado.get("/admin/inscricoes?status=finalizada")
    assert b"Aluno Fict\xc3\xadcio" in filtrada.data
    vazia = client_autenticado.get("/admin/inscricoes?status=cancelada")
    assert b"Aluno Fict\xc3\xadcio" not in vazia.data


def test_exportacao_gera_planilha_excel(client_autenticado):
    curso = criar_curso_gratuito()
    inscricao = InscricaoService().criar_pre_inscricao(
        curso.id,
        {
            "nome_completo": "Aluno Fictício",
            "cpf": "529.982.247-25",
            "email": "aluno@example.com",
        },
    )

    resposta = client_autenticado.get("/admin/inscricoes/exportar")

    assert resposta.status_code == 200
    assert resposta.mimetype == (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert "attachment;" in resposta.headers["Content-Disposition"]
    assert resposta.headers["Content-Disposition"].endswith('.xlsx"')

    planilha = load_workbook(BytesIO(resposta.data))
    aba = planilha.active
    assert aba.max_row == 2
    assert aba["A1"].value == "Protocolo"
    assert aba["A2"].value == inscricao.protocolo
    assert aba["B2"].value == "Aluno Fictício"
    assert aba["G2"].value == curso.titulo
