"""Application Factory da aplicação SENAC Cursos."""

from __future__ import annotations

from pathlib import Path

from flask import Flask

from app.blueprints import register_blueprints
from app.cli import registrar_comandos
from app.config import get_config
from app.errors import register_error_handlers
from app.extensions import csrf, db, login_manager, migrate


def create_app(config_name: str | None = None) -> Flask:
    """Cria e configura uma instância da aplicação Flask.

    Args:
        config_name: Nome do ambiente (``development``, ``testing`` ou
            ``production``). Quando omitido, usa ``FLASK_CONFIG`` ou
            ``development``.
    """
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(get_config(config_name))

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    _registrar_extensoes(app)
    _registrar_modelos()
    _registrar_carregador_de_usuario()
    register_blueprints(app)
    register_error_handlers(app)
    registrar_comandos(app)
    _registrar_contexto_do_shell(app)

    return app


def _registrar_extensoes(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)


def _registrar_modelos() -> None:
    # A importação garante que o SQLAlchemy e o Alembic conheçam os modelos.
    from app import models  # noqa: F401


def _registrar_carregador_de_usuario() -> None:
    from app.models import Administrador

    @login_manager.user_loader
    def carregar_administrador(usuario_id: str):
        try:
            identificador = int(usuario_id)
        except (TypeError, ValueError):
            return None
        return db.session.get(Administrador, identificador)


def _registrar_contexto_do_shell(app: Flask) -> None:
    from app.models import Administrador, Curso, Inscricao

    @app.shell_context_processor
    def contexto_do_shell() -> dict[str, object]:
        return {
            "db": db,
            "Administrador": Administrador,
            "Curso": Curso,
            "Inscricao": Inscricao,
        }
