"""Blueprint do catálogo de cursos."""

from flask import Blueprint

bp = Blueprint("catalogo", __name__, url_prefix="/cursos")

from app.blueprints.catalogo import routes  # noqa: E402,F401
