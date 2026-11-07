"""Tratadores de erro compartilhados."""

from __future__ import annotations

from flask import Flask, render_template
from flask_wtf.csrf import CSRFError

from app.extensions import db


def register_error_handlers(app: Flask) -> None:
    """Registra as páginas de erro da aplicação."""

    @app.errorhandler(400)
    def erro_400(erro):  # pragma: no cover - comportamento padrão do Flask
        return render_template("errors/400.html"), 400

    @app.errorhandler(403)
    def erro_403(erro):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def erro_404(erro):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def erro_500(erro):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    @app.errorhandler(CSRFError)
    def erro_csrf(erro):
        return render_template("errors/400.html", motivo=erro.description), 400
