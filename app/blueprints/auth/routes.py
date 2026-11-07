"""Pontos de integração da autenticação administrativa.

Implementação esperada:

- ``login`` (GET): renderizar o formulário de acesso.
- ``login`` (POST): validar CSRF, autenticar com
  ``Administrador.verificar_senha`` e chamar ``login_user``.
- ``logout`` (POST): chamar ``logout_user`` e redirecionar para ``main.index``.

O ``login_manager.login_view`` já aponta para ``auth.login``.
"""

from __future__ import annotations

from flask import abort, render_template

from app.blueprints.auth import bp


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Login do administrador. Contrato: responder em ``auth.login``."""
    return render_template("auth/login.html")


@bp.post("/logout")
def logout():
    """Logout do administrador. Contrato: responder em ``auth.logout``."""
    abort(501)
