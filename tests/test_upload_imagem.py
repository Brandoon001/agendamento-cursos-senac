"""Testes do upload de imagens no cadastro e edição de cursos."""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from app.extensions import db
from app.models import Curso
from app.services.curso_service import CursoService

PNG_VALIDO = b"\x89PNG\r\n\x1a\n" + b"conteudo-ficticio-de-imagem"


@pytest.fixture()
def uploads(app, tmp_path):
    pasta = tmp_path / "uploads"
    pasta.mkdir()
    app.config["UPLOAD_FOLDER"] = pasta
    return pasta


def dados_curso(**alteracoes):
    dados = {
        "titulo": "Curso com imagem",
        "descricao": "Descrição usada apenas nos testes de upload.",
        "cidade": "Sobral",
        "carga_horaria": "20",
        "vagas": "10",
        "ativo": "y",
    }
    dados.update(alteracoes)
    return dados


def arquivo(conteudo=PNG_VALIDO, nome="banner.png"):
    return (io.BytesIO(conteudo), nome)


def test_upload_salva_imagem_no_cadastro(client_autenticado, uploads):
    resposta = client_autenticado.post(
        "/admin/cursos/novo",
        data={**dados_curso(), "imagem_upload": arquivo()},
    )

    assert resposta.status_code == 302
    curso = db.session.scalar(
        db.select(Curso).where(Curso.titulo == "Curso com imagem")
    )
    assert curso is not None
    assert curso.imagem_url.startswith("/static/uploads/")

    nome = curso.imagem_url.removeprefix("/static/uploads/")
    assert (uploads / nome).read_bytes() == PNG_VALIDO


def test_upload_na_edicao_substitui_e_remove_imagem_antiga(
    client_autenticado, uploads
):
    (uploads / "antigo.png").write_bytes(PNG_VALIDO)
    curso = CursoService().criar_curso(
        dados_curso(imagem_url="/static/uploads/antigo.png")
    )

    resposta = client_autenticado.post(
        f"/admin/cursos/{curso.id}/editar",
        data={
            **dados_curso(),
            "imagem_url": "/static/uploads/antigo.png",
            "imagem_upload": arquivo(nome="novo.png"),
        },
    )

    assert resposta.status_code == 302
    assert curso.imagem_url != "/static/uploads/antigo.png"
    assert not (uploads / "antigo.png").exists()
    assert (uploads / curso.imagem_url.removeprefix("/static/uploads/")).is_file()


def test_upload_rejeita_conteudo_que_nao_e_imagem(client_autenticado, uploads):
    resposta = client_autenticado.post(
        "/admin/cursos/novo",
        data={
            **dados_curso(),
            "imagem_upload": arquivo(b"texto simples", "falso.png"),
        },
    )

    assert resposta.status_code == 200
    assert "não é uma imagem válida" in resposta.data.decode("utf-8")
    assert db.session.scalar(db.select(db.func.count()).select_from(Curso)) == 0
    assert list(uploads.iterdir()) == []


def test_upload_rejeita_extensao_nao_permitida(client_autenticado, uploads):
    resposta = client_autenticado.post(
        "/admin/cursos/novo",
        data={**dados_curso(), "imagem_upload": arquivo(nome="banner.txt")},
    )

    assert resposta.status_code == 200
    assert "PNG, JPG, GIF ou WebP" in resposta.data.decode("utf-8")
    assert list(uploads.iterdir()) == []


def test_edicao_mantem_url_local_de_imagem(client_autenticado, uploads):
    curso = CursoService().criar_curso(
        dados_curso(imagem_url="/static/uploads/banner.png")
    )

    resposta = client_autenticado.post(
        f"/admin/cursos/{curso.id}/editar",
        data={**dados_curso(), "imagem_url": "/static/uploads/banner.png"},
    )

    assert resposta.status_code == 302
    assert curso.imagem_url == "/static/uploads/banner.png"


def test_limpar_campo_de_imagem_remove_arquivo_local(client_autenticado, uploads):
    (uploads / "antigo.png").write_bytes(PNG_VALIDO)
    curso = CursoService().criar_curso(
        dados_curso(imagem_url="/static/uploads/antigo.png")
    )

    resposta = client_autenticado.post(
        f"/admin/cursos/{curso.id}/editar",
        data=dados_curso(imagem_url=""),
    )

    assert resposta.status_code == 302
    assert curso.imagem_url == ""
    assert not (uploads / "antigo.png").exists()


def test_excluir_curso_remove_imagem_local(client_autenticado, uploads):
    (uploads / "antigo.png").write_bytes(PNG_VALIDO)
    curso = CursoService().criar_curso(
        dados_curso(imagem_url="/static/uploads/antigo.png")
    )

    resposta = client_autenticado.post(f"/admin/cursos/{curso.id}/excluir")

    assert resposta.status_code == 302
    assert not (uploads / "antigo.png").exists()
