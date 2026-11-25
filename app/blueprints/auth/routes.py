"""Rotas de autenticação do administrador."""

from __future__ import annotations

from urllib.parse import urlsplit

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.blueprints.auth import bp
from app.forms.auth import LoginForm
from app.services.autenticacao_service import AutenticacaoService


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Exibe e processa o formulário de acesso ao painel."""
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    proximo = request.args.get("next", "")
    formulario = LoginForm()

    if formulario.validate_on_submit():
        administrador = AutenticacaoService().autenticar(
            formulario.email.data,
            formulario.senha.data,
        )
        if administrador is None:
            flash("E-mail ou senha inválidos.", "error")
        else:
            login_user(administrador)
            flash(f"Bem-vindo(a), {administrador.nome}!", "success")
            return redirect(_destino_seguro(proximo))

    return render_template("auth/login.html", formulario=formulario, proximo=proximo)


@bp.post("/logout")
@login_required
def logout():
    """Encerra a sessão administrativa."""
    logout_user()
    flash("Você saiu do painel administrativo.", "success")
    return redirect(url_for("main.index"))


def _destino_seguro(proximo: str) -> str:
    """Aceita apenas caminhos internos, sem esquema nem host (anti open redirect)."""
    partes = urlsplit(proximo)
    if partes.scheme or partes.netloc or not partes.path.startswith("/"):
        return url_for("admin.dashboard")
    if proximo.startswith("//") or proximo.startswith("/\\"):
        return url_for("admin.dashboard")
    return proximo
