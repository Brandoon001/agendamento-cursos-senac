"""Ponto de entrada WSGI para servidores de produção."""

import os

from app import create_app

app = create_app(os.getenv("FLASK_CONFIG", "production"))
