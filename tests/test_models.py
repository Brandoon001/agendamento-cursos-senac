"""Testes dos modelos compartilhados com dados fictícios."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import (
    Administrador,
    Curso,
    Inscricao,
    StatusInscricao,
    TipoCurso,
)


def test_administrador_gera_hash_de_senha(app):
    administrador = Administrador(
        nome="Administrador de Teste",
        email="admin@example.test",
    )
    administrador.definir_senha("senha-ficticia")

    assert administrador.senha_hash != "senha-ficticia"
    assert administrador.verificar_senha("senha-ficticia") is True
    assert administrador.verificar_senha("senha-errada") is False
    assert administrador.is_active is True


def test_curso_gratuito_aceita_pre_inscricao(app):
    curso = Curso(
        titulo="Curso Gratuito de Teste",
        descricao="Curso fictício usado apenas em testes.",
        tipo=TipoCurso.GRATUITO,
    )

    assert curso.e_gratuito is True
    assert curso.e_pago is False
    assert curso.aceita_pre_inscricao is True


def test_relacionamento_entre_curso_e_inscricao(app):
    curso = Curso(
        titulo="Curso Gratuito de Teste",
        descricao="Curso fictício usado apenas em testes.",
        tipo=TipoCurso.GRATUITO,
    )
    inscricao = Inscricao(
        curso=curso,
        nome_completo="Aluno Fictício",
        cpf="00000000000",
        email="aluno@example.test",
        status=StatusInscricao.RECEBIDA,
    )

    db.session.add(inscricao)
    db.session.commit()

    assert inscricao.id is not None
    assert inscricao.curso is curso
    assert inscricao in curso.inscricoes
    assert inscricao.administrador is None


def test_curso_pago_exige_link_externo(app):
    curso = Curso(
        titulo="Curso Pago sem Link",
        descricao="Curso fictício usado apenas em testes.",
        tipo=TipoCurso.PAGO,
    )

    db.session.add(curso)

    with pytest.raises(IntegrityError):
        db.session.commit()

    db.session.rollback()


def test_cpf_nao_pode_repetir_no_mesmo_curso(app):
    curso = Curso(
        titulo="Curso Gratuito de Teste",
        descricao="Curso fictício usado apenas em testes.",
        tipo=TipoCurso.GRATUITO,
    )
    db.session.add(curso)
    db.session.commit()

    for _ in range(2):
        db.session.add(
            Inscricao(
                curso=curso,
                nome_completo="Aluno Fictício",
                cpf="00000000000",
                email="aluno@example.test",
                status=StatusInscricao.RECEBIDA,
            )
        )

    with pytest.raises(IntegrityError):
        db.session.commit()

    db.session.rollback()


def test_status_de_inscricao_disponiveis():
    assert {status.value for status in StatusInscricao} == {
        "recebida",
        "em_analise",
        "contatada",
        "finalizada",
        "cancelada",
    }


def test_status_padrao_da_inscricao_e_recebida(app):
    curso = Curso(
        titulo="Curso Gratuito de Teste",
        descricao="Curso fictício usado apenas em testes.",
        tipo=TipoCurso.GRATUITO,
    )
    inscricao = Inscricao(
        curso=curso,
        nome_completo="Aluno Fictício",
    )

    db.session.add(inscricao)
    db.session.commit()

    assert inscricao.status is StatusInscricao.RECEBIDA


def test_cpf_email_e_telefone_sao_opcionais(app):
    curso = Curso(
        titulo="Curso Gratuito de Teste",
        descricao="Curso fictício usado apenas em testes.",
        tipo=TipoCurso.GRATUITO,
    )
    inscricao = Inscricao(
        curso=curso,
        nome_completo="Aluno Fictício",
    )

    db.session.add(inscricao)
    db.session.commit()

    assert inscricao.cpf is None
    assert inscricao.email is None
    assert inscricao.telefone is None


def test_exclusao_de_curso_com_inscricoes_e_impedida(app):
    curso = Curso(
        titulo="Curso Gratuito de Teste",
        descricao="Curso fictício usado apenas em testes.",
        tipo=TipoCurso.GRATUITO,
    )
    inscricao = Inscricao(
        curso=curso,
        nome_completo="Aluno Fictício",
        cpf="00000000000",
    )
    db.session.add(inscricao)
    db.session.commit()

    inscricao_id = inscricao.id
    db.session.delete(curso)

    with pytest.raises(IntegrityError):
        db.session.commit()

    db.session.rollback()

    assert db.session.get(Inscricao, inscricao_id) is not None


def test_exclusao_de_curso_sem_inscricoes_e_permitida(app):
    curso = Curso(
        titulo="Curso Gratuito de Teste",
        descricao="Curso fictício usado apenas em testes.",
        tipo=TipoCurso.GRATUITO,
    )
    db.session.add(curso)
    db.session.commit()

    curso_id = curso.id
    db.session.delete(curso)
    db.session.commit()

    assert db.session.get(Curso, curso_id) is None


def test_curso_com_inscricao_pode_ser_arquivado(app):
    curso = Curso(
        titulo="Curso Gratuito de Teste",
        descricao="Curso fictício usado apenas em testes.",
        tipo=TipoCurso.GRATUITO,
    )
    inscricao = Inscricao(
        curso=curso,
        nome_completo="Aluno Fictício",
    )
    db.session.add(inscricao)
    db.session.commit()

    curso.ativo = False
    db.session.commit()

    assert curso.aceita_pre_inscricao is False
    assert db.session.get(Inscricao, inscricao.id) is not None
