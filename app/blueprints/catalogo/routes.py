"""Rotas públicas do catálogo de cursos gratuitos de Sobral."""

from __future__ import annotations

from flask import abort, render_template, request

from app.blueprints.catalogo import bp
from app.services.curso_service import CursoService, curso_esta_visivel


@bp.get("/", strict_slashes=False)
def listar():
    """Lista pública de cursos gratuitos e ativos, com busca opcional."""
    termo = request.args.get("q", "").strip()

    servico = CursoService()
    cursos = servico.listar_cursos_publicos(termo=termo or None)

    return render_template(
        "catalogo/lista_cursos.html",
        cursos=cursos,
        termo=termo,
    )


@bp.get("/<int:curso_id>")
def detalhe(curso_id: int):
    """Detalhe público de um curso gratuito, ativo e de Sobral."""
    servico = CursoService()
    curso = servico.obter_curso(curso_id)

    if not curso_esta_visivel(curso):
        abort(404)

    turmas = servico.listar_turmas(curso_id, apenas_ativas=True)

    return render_template(
        "catalogo/detalhe_curso.html",
        curso=curso,
        turmas=turmas,
    )
