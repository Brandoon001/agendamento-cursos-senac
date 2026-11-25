"""Formulário público de pré-inscrição em cursos gratuitos."""

from __future__ import annotations

import re
from datetime import date

from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, HiddenField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError


def somente_digitos(valor: str) -> str:
    """Remove máscara e espaços de um documento ou telefone."""
    return re.sub(r"\D", "", valor or "")


def cpf_e_valido(cpf: str) -> bool:
    """Valida os dígitos verificadores de um CPF."""
    numeros = somente_digitos(cpf)
    if len(numeros) != 11 or len(set(numeros)) == 1:
        return False

    for posicao, peso in ((9, 10), (10, 11)):
        soma = sum(
            int(numero) * fator
            for numero, fator in zip(numeros[:posicao], range(peso, 1, -1))
        )
        resto = soma % 11
        verificador = 0 if resto < 2 else 11 - resto
        if int(numeros[posicao]) != verificador:
            return False
    return True


def formatar_cpf(cpf: str) -> str:
    """Devolve o CPF no formato 000.000.000-00."""
    numeros = somente_digitos(cpf)
    return f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:]}"


class InscricaoForm(FlaskForm):
    """Dados do candidato e aceite de tratamento de dados."""

    nome_completo = StringField(
        "Nome completo",
        validators=[
            DataRequired(message="Informe seu nome completo."),
            Length(
                min=3,
                max=150,
                message="O nome deve ter entre 3 e 150 caracteres.",
            ),
        ],
    )
    cpf = StringField(
        "CPF",
        validators=[
            DataRequired(message="Informe seu CPF."),
            Length(max=14, message="Informe um CPF válido."),
        ],
    )
    email = StringField(
        "E-mail",
        validators=[
            DataRequired(message="Informe seu e-mail."),
            Email(message="Informe um e-mail válido."),
            Length(max=255, message="O e-mail deve ter no máximo 255 caracteres."),
        ],
    )
    telefone = StringField(
        "Telefone",
        validators=[
            DataRequired(message="Informe seu telefone."),
            Length(max=20, message="O telefone deve ter no máximo 20 caracteres."),
        ],
    )
    data_nascimento = DateField(
        "Data de nascimento (opcional)",
        validators=[Optional()],
    )
    observacoes = TextAreaField(
        "Observações (opcional)",
        validators=[
            Optional(),
            Length(max=1000, message="Use no máximo 1000 caracteres."),
        ],
    )
    aceite = BooleanField(
        "Autorizo o tratamento dos meus dados para esta inscrição.",
        validators=[
            DataRequired(
                message="É necessário autorizar o tratamento dos seus dados."
            )
        ],
    )
    turma_id = HiddenField()

    def validate_cpf(self, campo) -> None:
        if campo.data and not cpf_e_valido(campo.data):
            raise ValidationError("Informe um CPF válido.")

    def validate_telefone(self, campo) -> None:
        digitos = somente_digitos(campo.data)
        if campo.data and len(digitos) not in (10, 11):
            raise ValidationError("Informe um telefone com DDD.")

    def validate_data_nascimento(self, campo) -> None:
        if campo.data and campo.data > date.today():
            raise ValidationError("A data de nascimento não pode ser futura.")
