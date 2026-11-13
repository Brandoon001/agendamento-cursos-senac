"""Rotas públicas do catálogo de cursos."""

from __future__ import annotations

from flask import abort, redirect, render_template, request

from app.blueprints.catalogo import bp
from app.models import TipoCurso
from app.services.curso_service import CursoService, curso_esta_visivel


@bp.get("/", strict_slashes=False)
def listar():
    """Lista pública de cursos ativos, com busca e filtro por tipo."""
    termo = request.args.get("q", "").strip()
    tipo = request.args.get("tipo", "").strip() or None

    try:
        tipo_selecionado = TipoCurso(tipo) if tipo else None
    except ValueError:
        tipo_selecionado = None

    servico = CursoService()
    cursos = servico.listar_cursos_publicos(
        termo=termo or None,
        tipo=tipo_selecionado,
    )

    return render_template(
        "catalogo/lista_cursos.html",
        cursos=cursos,
        termo=termo,
        tipo_selecionado=tipo_selecionado.value if tipo_selecionado else "",
        tipos=TipoCurso,
    )


@bp.get("/<int:curso_id>")
def detalhe(curso_id: int):
    """Detalhe público de um curso ativo, com suas turmas e vagas."""
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


@bp.get("/<int:curso_id>/comprar")
def comprar(curso_id: int):
    """Redireciona o visitante para o link externo de compra do curso pago."""
    servico = CursoService()
    curso = servico.obter_curso(curso_id)

    if (
        not curso_esta_visivel(curso)
        or not curso.e_pago
        or not curso.link_externo
    ):
        abort(404)

    return redirect(servico.obter_link_compra(curso))
