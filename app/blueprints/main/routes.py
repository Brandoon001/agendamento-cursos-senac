"""Rotas compartilhadas de entrada da aplicação."""

from __future__ import annotations

from flask import render_template

from app.blueprints.main import bp


@bp.get("/")
def index():
    """Página inicial que apresenta o sistema e os módulos disponíveis."""
    return render_template("main/index.html")
