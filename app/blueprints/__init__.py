"""Registro central dos Blueprints.

Cada módulo possui seu próprio pacote em ``app/blueprints`` e deve implementar
suas rotas dentro do respectivo arquivo ``routes.py``. Este arquivo é o único
ponto da fundação que precisa conhecer todos os Blueprints.
"""

from __future__ import annotations

from flask import Flask


def register_blueprints(app: Flask) -> None:
    """Registra todos os Blueprints da aplicação."""
    from app.blueprints.admin import bp as admin_bp
    from app.blueprints.auth import bp as auth_bp
    from app.blueprints.catalogo import bp as catalogo_bp
    from app.blueprints.inscricoes import bp as inscricoes_bp
    from app.blueprints.main import bp as main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(catalogo_bp)
    app.register_blueprint(inscricoes_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
