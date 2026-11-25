"""Formulário de acesso administrativo."""

from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField
from wtforms.validators import DataRequired, Email, Length


class LoginForm(FlaskForm):
    """Credenciais informadas no login do painel."""

    email = StringField(
        "E-mail",
        filters=[lambda valor: (valor or "").strip().lower()],
        validators=[
            DataRequired(message="Informe o e-mail."),
            Email(message="Informe um e-mail válido."),
            Length(max=255, message="O e-mail deve ter no máximo 255 caracteres."),
        ],
    )
    senha = PasswordField(
        "Senha",
        validators=[DataRequired(message="Informe a senha.")],
    )
