"""Instâncias compartilhadas das extensões Flask.

As extensões são criadas aqui sem uma aplicação vinculada e inicializadas no
Application Factory (``app.create_app``).
"""

import sqlite3

from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

login_manager.login_view = "auth.login"
login_manager.login_message = "Faça login para acessar o painel administrativo."
login_manager.login_message_category = "warning"
login_manager.session_protection = "strong"


@event.listens_for(Engine, "connect")
def _ativar_chaves_estrangeiras_sqlite(dbapi_connection, connection_record):
    """Garante a aplicação de FKs e ON DELETE no SQLite."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()
