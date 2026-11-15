"""Regras de validação e normalização dos dados da pré-inscrição.

Campos obrigatórios: nome_completo, email e telefone.
Campos opcionais: cpf (validado e checado contra duplicidade somente quando
informado), data_nascimento e observacoes.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Mapping

from email_validator import EmailNotValidError, validate_email

CAMPOS_OBRIGATORIOS = ("nome_completo", "email", "telefone")

NOME_MAX = 150
EMAIL_MAX = 255
OBSERVACOES_MAX = 1000
IDADE_MAXIMA_ANOS = 120


class CampoInvalido(ValueError):
    """Erro de validação de um único campo (mensagem pronta para o usuário)."""


def _texto(valor: object) -> str:
    return "" if valor is None else str(valor).strip()


def somente_digitos(valor: object) -> str:
    return re.sub(r"\D", "", _texto(valor))


def validar_nome(valor: object) -> str:
    nome = re.sub(r"\s+", " ", _texto(valor))
    if not nome:
        raise CampoInvalido("Informe o nome completo.")
    if len(nome) > NOME_MAX:
        raise CampoInvalido(f"O nome deve ter no máximo {NOME_MAX} caracteres.")
    if len(nome.split(" ")) < 2:
        raise CampoInvalido("Informe o nome completo (nome e sobrenome).")
    if any(c.isdigit() for c in nome):
        raise CampoInvalido("O nome não pode conter números.")
    return nome


def cpf_e_valido(digitos: str) -> bool:
    """Valida CPF pelos dígitos verificadores (11 dígitos, sem repetição)."""
    if len(digitos) != 11 or not digitos.isdigit() or len(set(digitos)) == 1:
        return False
    for tamanho in (9, 10):
        soma = sum(int(d) * p for d, p in zip(digitos[:tamanho], range(tamanho + 1, 1, -1)))
        verificador = (soma * 10) % 11 % 10
        if verificador != int(digitos[tamanho]):
            return False
    return True


def validar_cpf(valor: object) -> str | None:
    """Retorna o CPF só com dígitos, ou None quando não informado."""
    if not _texto(valor):
        return None
    digitos = somente_digitos(valor)
    if not cpf_e_valido(digitos):
        raise CampoInvalido("CPF inválido. Confira os números digitados.")
    return digitos


def validar_email(valor: object) -> str:
    texto = _texto(valor)
    if not texto:
        raise CampoInvalido("Informe o e-mail.")
    if len(texto) > EMAIL_MAX:
        raise CampoInvalido("E-mail muito longo.")
    try:
        resultado = validate_email(texto, check_deliverability=False)
    except EmailNotValidError:
        raise CampoInvalido("Informe um e-mail válido.") from None
    return resultado.normalized.lower()


def validar_telefone(valor: object) -> str:
    """Aceita DDD + 8/9 dígitos, com ou sem +55; devolve só dígitos."""
    if not _texto(valor):
        raise CampoInvalido("Informe o telefone.")
    digitos = somente_digitos(valor)
    if len(digitos) in (12, 13) and digitos.startswith("55"):
        digitos = digitos[2:]
    if len(digitos) not in (10, 11):
        raise CampoInvalido("Informe um telefone válido com DDD.")
    if digitos[0] == "0" or (len(digitos) == 11 and digitos[2] != "9"):
        raise CampoInvalido("Informe um telefone válido com DDD.")
    return digitos


def validar_data_nascimento(valor: object, hoje: date | None = None) -> date | None:
    if valor in (None, ""):
        return None
    if isinstance(valor, datetime):
        data = valor.date()
    elif isinstance(valor, date):
        data = valor
    else:
        try:
            data = datetime.strptime(_texto(valor), "%Y-%m-%d").date()
        except ValueError:
            raise CampoInvalido("Data de nascimento inválida.") from None
    hoje = hoje or date.today()
    if data > hoje:
        raise CampoInvalido("A data de nascimento não pode estar no futuro.")
    if (hoje.year - data.year) > IDADE_MAXIMA_ANOS:
        raise CampoInvalido("Data de nascimento inválida.")
    return data


def validar_observacoes(valor: object) -> str | None:
    texto = _texto(valor)
    if len(texto) > OBSERVACOES_MAX:
        raise CampoInvalido(
            f"As observações devem ter no máximo {OBSERVACOES_MAX} caracteres."
        )
    return texto or None


_VALIDADORES = {
    "nome_completo": validar_nome,
    "cpf": validar_cpf,
    "email": validar_email,
    "telefone": validar_telefone,
    "data_nascimento": validar_data_nascimento,
    "observacoes": validar_observacoes,
}


def validar_dados_inscricao(
    dados: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, str]]:
    """Valida e normaliza os dados; devolve (limpos, erros_por_campo)."""
    limpos: dict[str, object] = {}
    erros: dict[str, str] = {}
    for campo, validador in _VALIDADORES.items():
        try:
            limpos[campo] = validador(dados.get(campo))
        except CampoInvalido as erro:
            erros[campo] = str(erro)
    return limpos, erros