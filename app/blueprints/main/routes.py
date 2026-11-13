"""Rotas compartilhadas de entrada da aplicação."""

from __future__ import annotations

from flask import render_template

from app.blueprints.main import bp
from app.services.curso_service import CursoService


@bp.get("/")
def index():
    """Página inicial com os cursos em destaque do catálogo."""
    cursos = CursoService().listar_cursos_publicos()
    return render_template(
        "main/index.html",
        cursos=cursos[:6],
        total_cursos=len(cursos),
    )
