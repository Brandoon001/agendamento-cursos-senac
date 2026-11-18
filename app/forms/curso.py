"""Formulários administrativos do módulo de cursos."""

from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    IntegerField,
    StringField,
    TextAreaField,
    TimeField,
)
from wtforms.validators import (
    DataRequired,
    Length,
    NumberRange,
    Optional,
    URL,
    ValidationError,
)


class CursoForm(FlaskForm):
    """Cadastro e edição de cursos gratuitos do SENAC Sobral."""

    titulo = StringField(
        "Nome do curso",
        validators=[
            DataRequired(message="Informe o nome do curso."),
            Length(
                max=150,
                message="O nome deve ter no máximo 150 caracteres.",
            ),
        ],
    )
    slug = StringField(
        "Identificador na URL (opcional)",
        validators=[
            Optional(),
            Length(
                max=180,
                message="O identificador deve ter no máximo 180 caracteres.",
            ),
        ],
    )
    descricao = TextAreaField(
        "Descrição",
        validators=[
            DataRequired(message="Informe a descrição do curso."),
        ],
    )
    cidade = StringField(
        "Cidade",
        default="Sobral",
        validators=[
            DataRequired(message="Informe a cidade do curso."),
            Length(
                max=100,
                message="A cidade deve ter no máximo 100 caracteres.",
            ),
        ],
    )
    carga_horaria = IntegerField(
        "Carga horária (horas)",
        validators=[
            Optional(),
            NumberRange(
                min=1,
                message="A carga horária deve ser maior que zero.",
            ),
        ],
    )
    data_inicio = DateField(
        "Data de início",
        validators=[Optional()],
    )
    data_fim = DateField(
        "Data de término",
        validators=[Optional()],
    )
    vagas = IntegerField(
        "Vagas de referência",
        validators=[
            Optional(),
            NumberRange(
                min=0,
                message="A quantidade de vagas não pode ser negativa.",
            ),
        ],
    )
    imagem_url = StringField(
        "URL da imagem",
        validators=[
            Optional(),
            URL(message="Informe uma URL de imagem válida."),
            Length(
                max=500,
                message="A URL deve ter no máximo 500 caracteres.",
            ),
        ],
    )
    ativo = BooleanField("Curso ativo", default=True)

    def validate_data_fim(self, campo) -> None:
        if (
            campo.data
            and self.data_inicio.data
            and campo.data < self.data_inicio.data
        ):
            raise ValidationError(
                "A data de término não pode ser anterior à data de início."
            )


class TurmaForm(FlaskForm):
    """Cadastro e edição de turmas e horários de um curso."""

    nome = StringField(
        "Nome ou código da turma",
        validators=[
            DataRequired(message="Informe o nome ou código da turma."),
            Length(
                max=100,
                message="O nome deve ter no máximo 100 caracteres.",
            ),
        ],
    )
    dias_semana = StringField(
        "Dias da semana",
        validators=[
            Optional(),
            Length(
                max=120,
                message="Os dias devem ter no máximo 120 caracteres.",
            ),
        ],
    )
    hora_inicio = TimeField(
        "Horário de início",
        validators=[Optional()],
    )
    hora_fim = TimeField(
        "Horário de término",
        validators=[Optional()],
    )
    data_inicio = DateField(
        "Data de início",
        validators=[Optional()],
    )
    data_fim = DateField(
        "Data de término",
        validators=[Optional()],
    )
    vagas = IntegerField(
        "Quantidade de vagas",
        validators=[
            Optional(),
            NumberRange(
                min=0,
                message="A quantidade de vagas não pode ser negativa.",
            ),
        ],
    )
    ativo = BooleanField("Turma ativa", default=True)

    def validate_hora_fim(self, campo) -> None:
        if (
            campo.data
            and self.hora_inicio.data
            and campo.data <= self.hora_inicio.data
        ):
            raise ValidationError(
                "O horário de término deve ser posterior ao de início."
            )

    def validate_data_fim(self, campo) -> None:
        if (
            campo.data
            and self.data_inicio.data
            and campo.data < self.data_inicio.data
        ):
            raise ValidationError(
                "A data de término não pode ser anterior à data de início."
            )

    def validate_hora_inicio(self, campo) -> None:
        if bool(campo.data) != bool(self.hora_fim.data):
            raise ValidationError(
                "Informe o horário de início e de término."
            )
