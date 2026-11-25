"""Testes do módulo de cursos, turmas e controle de vagas."""

from __future__ import annotations

from datetime import date, time

import pytest

from app.extensions import db
from app.models import Curso, Inscricao, StatusInscricao, TipoCurso, Turma
from app.services.curso_service import CursoService


def dados_curso(**alteracoes):
    dados = {
        "titulo": "Curso Fictício de Teste",
        "descricao": "Conteúdo fictício usado apenas em testes.",
        "cidade": "Sobral",
        "carga_horaria": 20,
        "vagas": 10,
        "ativo": True,
    }
    dados.update(alteracoes)
    return dados


def dados_turma(**alteracoes):
    dados = {
        "nome": "Turma Teste",
        "dias_semana": "Segunda e quarta",
        "hora_inicio": time(18, 0),
        "hora_fim": time(20, 0),
        "vagas": 5,
        "ativo": True,
    }
    dados.update(alteracoes)
    return dados


def test_servico_cria_curso_gratuito_e_gera_slug(app):
    curso = CursoService().criar_curso(
        dados_curso(titulo="Excel Básico")
    )

    assert curso.id is not None
    assert curso.slug == "excel-basico"
    assert curso.tipo is TipoCurso.GRATUITO
    assert curso.ativo is True


def test_servico_gera_slug_unico(app):
    servico = CursoService()
    primeiro = servico.criar_curso(dados_curso(titulo="Curso Repetido"))
    segundo = servico.criar_curso(dados_curso(titulo="Curso Repetido"))

    assert primeiro.slug == "curso-repetido"
    assert segundo.slug == "curso-repetido-2"


def test_servico_cria_curso_em_outra_cidade_quando_informado(app):
    curso = CursoService().criar_curso(
        dados_curso(titulo="Curso em Fortaleza", cidade="Fortaleza")
    )

    assert curso.cidade == "Fortaleza"
    assert curso.tipo is TipoCurso.GRATUITO


def test_servico_ignora_campos_de_curso_pago(app):
    curso = CursoService().criar_curso(
        dados_curso(
            tipo="pago",
            link_externo="https://example.test/compra",
            valor="350.00",
        )
    )

    assert curso.tipo is TipoCurso.GRATUITO
    assert curso.link_externo is None
    assert curso.valor is None


def test_ativacao_e_desativacao_do_curso(app):
    servico = CursoService()
    curso = servico.criar_curso(dados_curso())

    servico.definir_situacao(curso, False)
    assert curso.ativo is False
    assert curso.possui_vagas is False
    assert servico.listar_cursos_publicos() == []

    servico.definir_situacao(curso, True)
    assert curso.ativo is True
    assert curso.possui_vagas is True
    assert [item.id for item in servico.listar_cursos_publicos()] == [curso.id]


def test_curso_aceita_turmas_com_horarios_diferentes(app):
    servico = CursoService()
    curso = servico.criar_curso(dados_curso())

    manha = servico.criar_turma(
        curso.id,
        dados_turma(
            nome="Turma Manhã",
            hora_inicio=time(8, 0),
            hora_fim=time(10, 0),
        ),
    )
    noite = servico.criar_turma(
        curso.id,
        dados_turma(
            nome="Turma Noite",
            hora_inicio=time(19, 0),
            hora_fim=time(21, 30),
        ),
    )

    turmas = servico.listar_turmas(curso.id)

    assert {turma.id for turma in turmas} == {manha.id, noite.id}
    assert manha.curso is curso
    assert noite.horario_formatado == "19:00 às 21:30"


def test_controle_de_vagas_por_turma(app):
    servico = CursoService()
    curso = servico.criar_curso(dados_curso())
    turma = servico.criar_turma(curso.id, dados_turma(vagas=2))

    db.session.add(
        Inscricao(
            curso=curso,
            turma=turma,
            nome_completo="Aluno Fictício Um",
            status=StatusInscricao.RECEBIDA,
        )
    )
    db.session.add(
        Inscricao(
            curso=curso,
            turma=turma,
            nome_completo="Aluno Fictício Dois",
            status=StatusInscricao.CANCELADA,
        )
    )
    db.session.commit()

    assert turma.vagas_ocupadas == 1
    assert turma.vagas_disponiveis == 1
    assert turma.tem_vagas is True

    db.session.add(
        Inscricao(
            curso=curso,
            turma=turma,
            nome_completo="Aluno Fictício Três",
            status=StatusInscricao.RECEBIDA,
        )
    )
    db.session.commit()

    assert turma.vagas_ocupadas == 2
    assert turma.vagas_disponiveis == 0
    assert turma.tem_vagas is False
    assert turma.disponivel is False


def test_turma_com_inscricoes_nao_pode_ser_excluida(app):
    servico = CursoService()
    curso = servico.criar_curso(dados_curso())
    turma = servico.criar_turma(curso.id, dados_turma())

    db.session.add(
        Inscricao(
            curso=curso,
            turma=turma,
            nome_completo="Aluno Fictício",
        )
    )
    db.session.commit()

    with pytest.raises(ValueError, match="possui inscrições"):
        servico.excluir_turma(turma)

    assert db.session.get(Turma, turma.id) is not None


def test_catalogo_lista_somente_cursos_ativos(client, app):
    servico = CursoService()
    ativo = servico.criar_curso(dados_curso(titulo="Curso Ativo Fictício"))
    inativo = servico.criar_curso(dados_curso(titulo="Curso Inativo Fictício"))
    servico.definir_situacao(inativo, False)

    resposta = client.get("/cursos")

    assert resposta.status_code == 200
    assert b"Curso Ativo Fict" in resposta.data
    assert b"Curso Inativo Fict" not in resposta.data
    assert ativo.ativo is True


def test_catalogo_lista_apenas_cursos_de_sobral(client, app):
    servico = CursoService()
    servico.criar_curso(dados_curso(titulo="Curso de Sobral Filtro"))
    servico.criar_curso(
        dados_curso(
            titulo="Curso de Fortaleza Filtro",
            cidade="Fortaleza",
        )
    )

    resposta = client.get("/cursos")

    assert b"Curso de Sobral Filtro" in resposta.data
    assert b"Curso de Fortaleza Filtro" not in resposta.data


def test_catalogo_busca_por_nome(client, app):
    servico = CursoService()
    servico.criar_curso(dados_curso(titulo="Excel Avançado Fictício"))
    servico.criar_curso(dados_curso(titulo="Informática Básica Fictícia"))

    resposta = client.get("/cursos?q=Excel")

    assert b"Excel Avan" in resposta.data
    assert "Informática Básica".encode() not in resposta.data


def test_detalhe_exibe_turmas_e_vagas(client, app):
    servico = CursoService()
    curso = servico.criar_curso(dados_curso(titulo="Curso Detalhado Fictício"))
    turma = servico.criar_turma(
        curso.id,
        dados_turma(nome="Turma Detalhada", vagas=3),
    )
    db.session.add(
        Inscricao(
            curso=curso,
            turma=turma,
            nome_completo="Aluno Fictício",
        )
    )
    db.session.commit()

    resposta = client.get(f"/cursos/{curso.id}")

    assert resposta.status_code == 200
    assert b"Turma Detalhada" in resposta.data
    assert b"2 de 3" in resposta.data
    assert f"/inscricoes/{curso.id}/pre-inscricao?turma_id={turma.id}".encode() in resposta.data


def test_detalhe_de_curso_inativo_retorna_404(client, app):
    servico = CursoService()
    curso = servico.criar_curso(dados_curso())
    servico.definir_situacao(curso, False)

    resposta = client.get(f"/cursos/{curso.id}")

    assert resposta.status_code == 404


def test_rota_de_compra_de_curso_pago_nao_existe(client, app):
    servico = CursoService()
    curso = servico.criar_curso(dados_curso())

    resposta = client.get(f"/cursos/{curso.id}/comprar")

    assert resposta.status_code == 404


def test_admin_de_cursos_exige_autenticacao(client):
    resposta = client.get("/admin/cursos")

    assert resposta.status_code == 302
    assert "/auth/login" in resposta.headers["Location"]


def test_admin_cadastra_curso(client_autenticado, app):
    resposta = client_autenticado.post(
        "/admin/cursos/novo",
        data={
            "titulo": "Curso Administrativo Fictício",
            "descricao": "Curso criado pelo painel em teste.",
            "cidade": "Sobral",
            "carga_horaria": "30",
            "vagas": "12",
            "ativo": "y",
        },
    )

    assert resposta.status_code == 302
    curso = db.session.scalar(
        db.select(Curso).where(
            Curso.titulo == "Curso Administrativo Fictício"
        )
    )
    assert curso is not None
    assert curso.carga_horaria == 30
    assert curso.vagas == 12
    assert resposta.headers["Location"].endswith(f"/admin/cursos/{curso.id}/turmas")


def test_admin_exige_cidade_do_curso(client_autenticado, app):
    resposta = client_autenticado.post(
        "/admin/cursos/novo",
        data={
            "titulo": "Curso Sem Cidade Inválido",
            "descricao": "Curso sem cidade não pode ser cadastrado.",
            "cidade": "   ",
            "ativo": "y",
        },
    )

    assert resposta.status_code == 200
    assert b"cidade" in resposta.data.lower()
    assert (
        db.session.scalar(
            db.select(Curso).where(Curso.titulo == "Curso Sem Cidade Inválido")
        )
        is None
    )


def test_admin_paginas_de_cursos_renderizam(client_autenticado, app):
    servico = CursoService()
    curso = servico.criar_curso(dados_curso())
    turma = servico.criar_turma(curso.id, dados_turma())

    paginas = [
        "/admin/",
        "/admin/cursos",
        "/admin/cursos/novo",
        f"/admin/cursos/{curso.id}/editar",
        f"/admin/cursos/{curso.id}/turmas",
        f"/admin/cursos/{curso.id}/turmas/nova",
        f"/admin/turmas/{turma.id}/editar",
    ]

    for pagina in paginas:
        resposta = client_autenticado.get(pagina)
        assert resposta.status_code == 200, pagina


def test_admin_edita_curso(client_autenticado, app):
    curso = CursoService().criar_curso(dados_curso())

    resposta = client_autenticado.post(
        f"/admin/cursos/{curso.id}/editar",
        data={
            "titulo": "Curso Editado Fictício",
            "descricao": "Descrição atualizada no teste.",
            "cidade": "Sobral",
            "carga_horaria": "40",
            "vagas": "20",
            "ativo": "y",
        },
    )

    assert resposta.status_code == 302
    db.session.refresh(curso)
    assert curso.titulo == "Curso Editado Fictício"
    assert curso.carga_horaria == 40
    assert curso.vagas == 20


def test_admin_ativa_e_desativa_curso(client_autenticado, app):
    curso = CursoService().criar_curso(dados_curso())

    resposta = client_autenticado.post(f"/admin/cursos/{curso.id}/desativar")
    assert resposta.status_code == 302
    db.session.refresh(curso)
    assert curso.ativo is False

    client_autenticado.post(f"/admin/cursos/{curso.id}/ativar")
    db.session.refresh(curso)
    assert curso.ativo is True


def test_admin_nao_exclui_curso_com_inscricoes(client_autenticado, app):
    curso = CursoService().criar_curso(dados_curso())
    db.session.add(
        Inscricao(curso=curso, nome_completo="Aluno Fictício")
    )
    db.session.commit()

    resposta = client_autenticado.post(
        f"/admin/cursos/{curso.id}/excluir",
        follow_redirects=True,
    )

    assert resposta.status_code == 200
    assert b"possui inscri" in resposta.data
    assert db.session.get(Curso, curso.id) is not None


def test_admin_exclui_curso_sem_inscricoes(client_autenticado, app):
    curso = CursoService().criar_curso(dados_curso())
    curso_id = curso.id

    resposta = client_autenticado.post(
        f"/admin/cursos/{curso_id}/excluir",
        follow_redirects=True,
    )

    assert resposta.status_code == 200
    assert db.session.get(Curso, curso_id) is None


def test_admin_gerencia_turma(client_autenticado, app):
    curso = CursoService().criar_curso(dados_curso())

    resposta = client_autenticado.post(
        f"/admin/cursos/{curso.id}/turmas/nova",
        data={
            "nome": "Turma Administrativa Fictícia",
            "dias_semana": "Terça e quinta",
            "hora_inicio": "18:30",
            "hora_fim": "21:00",
            "vagas": "15",
            "ativo": "y",
        },
    )

    assert resposta.status_code == 302
    turma = db.session.scalar(
        db.select(Turma).where(
            Turma.nome == "Turma Administrativa Fictícia"
        )
    )
    assert turma is not None
    assert turma.curso_id == curso.id
    assert turma.vagas == 15
    assert turma.hora_inicio == time(18, 30)

    resposta = client_autenticado.post(
        f"/admin/turmas/{turma.id}/editar",
        data={
            "nome": "Turma Administrativa Editada",
            "dias_semana": "Sábado",
            "hora_inicio": "08:00",
            "hora_fim": "12:00",
            "vagas": "8",
            "ativo": "y",
        },
    )
    assert resposta.status_code == 302
    db.session.refresh(turma)
    assert turma.nome == "Turma Administrativa Editada"
    assert turma.vagas == 8

    client_autenticado.post(f"/admin/turmas/{turma.id}/desativar")
    db.session.refresh(turma)
    assert turma.ativo is False

    client_autenticado.post(f"/admin/turmas/{turma.id}/ativar")
    db.session.refresh(turma)
    assert turma.ativo is True


def test_integracao_vagas_refletem_inscricoes_no_catalogo(client, app):
    servico = CursoService()
    curso = servico.criar_curso(dados_curso(titulo="Curso Integração Fictício"))
    turma = servico.criar_turma(curso.id, dados_turma(vagas=1))

    assert b"1 de 1" in client.get(f"/cursos/{curso.id}").data

    db.session.add(
        Inscricao(
            curso=curso,
            turma=turma,
            nome_completo="Aluno Fictício",
            status=StatusInscricao.RECEBIDA,
        )
    )
    db.session.commit()

    resposta = client.get(f"/cursos/{curso.id}")

    assert b"0 de 1" in resposta.data
    assert b"Vagas esgotadas" in resposta.data

    resposta_pre_inscricao = client.get(
        f"/inscricoes/{curso.id}/pre-inscricao?turma_id={turma.id}"
    )
    assert resposta_pre_inscricao.status_code == 200


def test_pagina_inicial_exibe_cursos_ativos(client, app):
    servico = CursoService()
    servico.criar_curso(dados_curso(titulo="Curso Home Fictício"))

    resposta = client.get("/")

    assert resposta.status_code == 200
    assert b"Curso Home Fict" in resposta.data


def test_turma_valida_horario_e_periodo(app):
    servico = CursoService()
    curso = servico.criar_curso(dados_curso())

    with pytest.raises(ValueError, match="posterior"):
        servico.criar_turma(
            curso.id,
            dados_turma(hora_inicio=time(20, 0), hora_fim=time(18, 0)),
        )

    with pytest.raises(ValueError, match="anterior"):
        servico.criar_turma(
            curso.id,
            dados_turma(
                data_inicio=date(2026, 2, 1),
                data_fim=date(2026, 1, 1),
            ),
        )


def test_servico_atualiza_curso_e_preserva_slug(app):
    servico = CursoService()
    curso = servico.criar_curso(dados_curso(titulo="Curso Atualizável"))
    slug_original = curso.slug

    atualizado = servico.atualizar_curso(
        curso,
        dados_curso(
            titulo="Curso Atualizável",
            cidade="Sobral",
            carga_horaria="25",
        ),
    )

    assert atualizado.id == curso.id
    assert atualizado.slug == slug_original
    assert atualizado.cidade == "Sobral"
    assert atualizado.carga_horaria == 25


def test_servico_exige_descricao_do_curso(app):
    with pytest.raises(ValueError, match="descri"):
        CursoService().criar_curso(dados_curso(descricao="   "))


def test_servico_rejeita_cidade_muito_longa(app):
    with pytest.raises(ValueError, match="cidade"):
        CursoService().criar_curso(
            dados_curso(cidade="Cidade " + "a" * 100)
        )


def test_servico_rejeita_data_em_formato_invalido(app):
    with pytest.raises(ValueError, match="data"):
        CursoService().criar_curso(
            dados_curso(data_inicio="31/12/2026")
        )


def test_inscricao_cancelada_volta_a_liberar_vaga(app):
    servico = CursoService()
    curso = servico.criar_curso(dados_curso())
    turma = servico.criar_turma(curso.id, dados_turma(vagas=1))
    inscricao = Inscricao(
        curso=curso,
        turma=turma,
        nome_completo="Aluno Fictício",
        status=StatusInscricao.RECEBIDA,
    )
    db.session.add(inscricao)
    db.session.commit()

    assert turma.vagas_disponiveis == 0
    assert turma.disponivel is False

    inscricao.status = StatusInscricao.CANCELADA
    db.session.commit()
    db.session.refresh(turma)

    assert turma.vagas_ocupadas == 0
    assert turma.vagas_disponiveis == 1
    assert turma.disponivel is True


def test_disponibilidade_do_curso_soma_turmas_ativas(app):
    servico = CursoService()
    curso = servico.criar_curso(dados_curso())
    manha = servico.criar_turma(
        curso.id,
        dados_turma(nome="Turma Manhã", vagas=2),
    )
    noite = servico.criar_turma(
        curso.id,
        dados_turma(nome="Turma Noite", vagas=3),
    )

    db.session.add_all(
        [
            Inscricao(curso=curso, turma=manha, nome_completo="Aluno A"),
            Inscricao(curso=curso, turma=manha, nome_completo="Aluno B"),
            Inscricao(curso=curso, turma=noite, nome_completo="Aluno C"),
        ]
    )
    db.session.commit()
    db.session.refresh(curso)

    assert manha.vagas_disponiveis == 0
    assert noite.vagas_disponiveis == 2
    assert curso.vagas_disponiveis == 2
    assert curso.possui_vagas is True

    db.session.add_all(
        [
            Inscricao(curso=curso, turma=noite, nome_completo="Aluno D"),
            Inscricao(curso=curso, turma=noite, nome_completo="Aluno E"),
        ]
    )
    db.session.commit()
    db.session.refresh(curso)
    db.session.refresh(manha)
    db.session.refresh(noite)

    assert curso.vagas_disponiveis == 0
    assert curso.possui_vagas is False
    assert manha.disponivel is False
    assert noite.disponivel is False


def test_detalhe_oculta_turma_inativa_e_nao_oferece_pre_inscricao(
    client,
    app,
):
    servico = CursoService()
    curso = servico.criar_curso(
        dados_curso(titulo="Curso Esgotado Fictício")
    )
    ativa = servico.criar_turma(
        curso.id,
        dados_turma(nome="Turma Ativa Fictícia", vagas=1),
    )
    inativa = servico.criar_turma(
        curso.id,
        dados_turma(nome="Turma Inativa Fictícia", vagas=5),
    )
    servico.definir_situacao_turma(inativa, False)
    db.session.add(
        Inscricao(
            curso=curso,
            turma=ativa,
            nome_completo="Aluno Fictício",
            status=StatusInscricao.RECEBIDA,
        )
    )
    db.session.commit()

    resposta = client.get(f"/cursos/{curso.id}")

    assert resposta.status_code == 200
    assert b"Turma Ativa Fict" in resposta.data
    assert b"Turma Inativa Fict" not in resposta.data
    assert b"Vagas esgotadas" in resposta.data
    assert f"/inscricoes/{curso.id}/pre-inscricao".encode() not in resposta.data


def test_card_oculta_pre_inscricao_quando_nao_ha_vagas(client, app):
    servico = CursoService()
    curso = servico.criar_curso(
        dados_curso(titulo="Curso Card Sem Vagas", vagas=1)
    )
    db.session.add(
        Inscricao(
            curso=curso,
            nome_completo="Aluno Fictício",
            status=StatusInscricao.RECEBIDA,
        )
    )
    db.session.commit()

    resposta = client.get("/cursos")

    assert b"Curso Card Sem Vagas" in resposta.data
    assert b"Vagas esgotadas" in resposta.data
    assert f"/inscricoes/{curso.id}/pre-inscricao".encode() not in resposta.data


def test_detalhe_de_curso_fora_de_sobral_retorna_404(client, app):
    servico = CursoService()
    curso = servico.criar_curso(
        dados_curso(
            titulo="Curso de Outra Cidade Fictício",
            cidade="Fortaleza",
        )
    )

    resposta = client.get(f"/cursos/{curso.id}")

    assert resposta.status_code == 404


def test_admin_nao_exclui_turma_com_inscricoes(client_autenticado, app):
    servico = CursoService()
    curso = servico.criar_curso(dados_curso())
    turma = servico.criar_turma(curso.id, dados_turma())
    db.session.add(
        Inscricao(curso=curso, turma=turma, nome_completo="Aluno Fictício")
    )
    db.session.commit()

    resposta = client_autenticado.post(
        f"/admin/turmas/{turma.id}/excluir",
        follow_redirects=True,
    )

    assert resposta.status_code == 200
    assert b"possui inscri" in resposta.data
    assert db.session.get(Turma, turma.id) is not None


def test_admin_valida_datas_do_curso(client_autenticado, app):
    resposta = client_autenticado.post(
        "/admin/cursos/novo",
        data={
            "titulo": "Curso com Datas Inválidas",
            "descricao": "Curso fictício com período invertido.",
            "cidade": "Sobral",
            "data_inicio": "2026-02-01",
            "data_fim": "2026-01-01",
            "ativo": "y",
        },
    )

    assert resposta.status_code == 200
    assert b"anterior" in resposta.data
    assert (
        db.session.scalar(
            db.select(Curso).where(
                Curso.titulo == "Curso com Datas Inválidas"
            )
        )
        is None
    )


def test_admin_valida_horario_da_turma(client_autenticado, app):
    curso = CursoService().criar_curso(dados_curso())

    resposta = client_autenticado.post(
        f"/admin/cursos/{curso.id}/turmas/nova",
        data={
            "nome": "Turma com Horário Inválido",
            "hora_inicio": "20:00",
            "hora_fim": "18:00",
            "vagas": "10",
            "ativo": "y",
        },
    )

    assert resposta.status_code == 200
    assert b"posterior" in resposta.data
    assert CursoService().listar_turmas(curso.id) == []


@pytest.mark.parametrize(
    ("metodo", "rota"),
    [
        ("get", "/admin/cursos/novo"),
        ("get", "/admin/cursos/1/editar"),
        ("get", "/admin/cursos/1/turmas"),
        ("post", "/admin/cursos/1/desativar"),
        ("post", "/admin/turmas/1/desativar"),
    ],
)
def test_rotas_administrativas_do_modulo_estao_protegidas(
    client,
    metodo,
    rota,
):
    resposta = getattr(client, metodo)(rota)

    assert resposta.status_code == 302
    assert "/auth/login" in resposta.headers["Location"]


def test_contrato_de_integracao_expoe_dados_de_curso_e_turma(app):
    servico = CursoService()
    curso = servico.criar_curso(
        dados_curso(titulo="Curso Integração Contrato")
    )
    turma = servico.criar_turma(
        curso.id,
        dados_turma(nome="Turma Integração", vagas=4),
    )

    assert curso.id is not None
    assert curso.titulo == "Curso Integração Contrato"
    assert curso.situacao == "ativo"
    assert turma.id is not None
    assert turma.nome == "Turma Integração"
    assert turma.curso_id == curso.id
    assert turma.horario_formatado == "18:00 às 20:00"
    assert turma.situacao == "ativa"
    assert turma.vagas_disponiveis == 4
    assert turma.tem_vagas is True
    assert turma.disponivel is True

    servico.definir_situacao_turma(turma, False)

    assert turma.situacao == "inativa"
    assert turma.disponivel is False


def test_admin_exclui_curso_com_turmas_sem_inscricoes(
    client_autenticado,
    app,
):
    servico = CursoService()
    curso = servico.criar_curso(dados_curso())
    turma = servico.criar_turma(curso.id, dados_turma())
    curso_id = curso.id
    turma_id = turma.id

    resposta = client_autenticado.post(
        f"/admin/cursos/{curso_id}/excluir",
        follow_redirects=True,
    )

    assert resposta.status_code == 200
    assert db.session.get(Curso, curso_id) is None
    assert db.session.get(Turma, turma_id) is None


def test_turma_de_curso_inativo_nao_esta_disponivel(app):
    servico = CursoService()
    curso = servico.criar_curso(dados_curso())
    turma = servico.criar_turma(curso.id, dados_turma(vagas=5))

    assert turma.disponivel is True
    assert servico.listar_turmas_disponiveis(curso.id) == [turma]

    servico.definir_situacao(curso, False)

    assert turma.disponivel is False
    assert turma.tem_vagas is True
    assert servico.listar_turmas_disponiveis(curso.id) == []

    servico.definir_situacao(curso, True)

    assert turma.disponivel is True
