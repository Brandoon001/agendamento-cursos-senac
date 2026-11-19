
"""Rotas públicas do catálogo de cursos."""

from __future__ import annotations

from flask import abort, redirect, render_template

from app.blueprints.catalogo import bp
from app.models import Curso
from app.models.enums import TipoCurso


@bp.get("/")
def listar():
    """Lista somente os cursos ativos."""

    cursos = (
        Curso.query
        .filter_by(ativo=True)
        .order_by(Curso.titulo.asc())
        .all()
    )

    return render_template(
        "catalogo/lista_cursos.html",
        cursos=cursos,
        tipo_curso=TipoCurso,
    )


@bp.get("/<int:curso_id>")
def detalhe(curso_id: int):
    """Exibe os detalhes do curso ou direciona para compra."""

    curso = Curso.query.filter_by(
        id=curso_id,
        ativo=True,
    ).first()

    if curso is None:
        abort(404)

    # Cursos pagos direcionam para o link externo.
    if curso.tipo == TipoCurso.PAGO and curso.link_externo:
        return redirect(curso.link_externo)

    return render_template(
        "catalogo/detalhe_curso.html",
        curso=curso,
    )
