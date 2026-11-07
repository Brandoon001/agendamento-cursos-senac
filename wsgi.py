"""Ponto de entrada WSGI para servidores de produção."""

from app import create_app

app = create_app()
