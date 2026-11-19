"""Formulário público de pré-inscrição."""

import re
from datetime import date

from flask_wtf import FlaskForm
from wtforms import DateField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, ValidationError


class PreInscricaoForm(FlaskForm):
    nome_completo = StringField(
        "Nome completo",
        validators=[
            DataRequired(message="Informe seu nome completo."),
            Length(max=150),
        ],
    )

    cpf = StringField(
        "CPF",
        validators=[
            DataRequired(message="Informe seu CPF."),
            Length(max=14),
        ],
    )

    email = StringField(
        "E-mail",
        validators=[
            DataRequired(message="Informe seu e-mail."),
            Email(message="Informe um endereço de e-mail válido."),
            Length(max=255),
        ],
    )

    telefone = StringField(
        "Telefone",
        validators=[
            DataRequired(message="Informe seu telefone."),
            Length(max=20),
        ],
    )

    data_nascimento = DateField(
        "Data de nascimento",
        format="%Y-%m-%d",
        validators=[
            DataRequired(message="Informe sua data de nascimento.")
        ],
    )

    observacoes = TextAreaField(
        "Observações",
        validators=[Length(max=2000)],
    )

    submit = SubmitField("Enviar pré-inscrição")

    def validate_nome_completo(self, field):
        nome = " ".join((field.data or "").split())

        if len(nome) < 3 or not any(letra.isalpha() for letra in nome):
            raise ValidationError("Informe um nome completo válido.")

        field.data = nome

    def validate_cpf(self, field):
        numeros = re.sub(r"\D", "", field.data or "")

        if len(numeros) != 11:
            raise ValidationError("O CPF deve conter 11 números.")

        field.data = numeros

    def validate_telefone(self, field):
        numeros = re.sub(r"\D", "", field.data or "")

        if not 10 <= len(numeros) <= 11:
            raise ValidationError(
                "Informe um telefone com DDD (10 ou 11 números)."
            )

        field.data = numeros

    def validate_data_nascimento(self, field):
        if field.data and field.data >= date.today():
            raise ValidationError(
                "A data de nascimento deve ser anterior a hoje."
            )