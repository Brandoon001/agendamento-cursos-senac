"""Blueprint das pré-inscrições em cursos gratuitos."""

from flask import Blueprint

bp = Blueprint("inscricoes", __name__, url_prefix="/inscricoes")

from app.blueprints.inscricoes import routes  # noqa: E402,F401
