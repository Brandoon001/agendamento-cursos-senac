"""Geração da planilha de inscrições para download administrativo."""

from __future__ import annotations

from io import BytesIO
from typing import Iterable

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from app.models import Inscricao

CABECALHOS = (
    "Protocolo",
    "Nome completo",
    "CPF",
    "E-mail",
    "Telefone",
    "Nascimento",
    "Curso",
    "Turma",
    "Situação",
    "Registrada em",
    "Observações",
)

LARGURAS = (18, 32, 17, 32, 18, 14, 38, 24, 16, 21, 45)
PREFIXOS_FORMULA = ("=", "+", "-", "@")


def gerar_planilha_inscricoes(inscricoes: Iterable[Inscricao]) -> bytes:
    """Monta um arquivo XLSX com as inscrições já filtradas na tela."""
    planilha = Workbook()
    aba = planilha.active
    aba.title = "Inscrições"
    aba.append(list(CABECALHOS))

    for celula in aba[1]:
        celula.font = Font(bold=True, color="FFFFFF")
        celula.fill = PatternFill(fill_type="solid", fgColor="004B8D")
        celula.alignment = Alignment(vertical="center")

    for inscricao in inscricoes:
        linha = [
            inscricao.protocolo,
            inscricao.nome_completo,
            inscricao.cpf or "",
            inscricao.email or "",
            inscricao.telefone or "",
            (
                inscricao.data_nascimento.strftime("%d/%m/%Y")
                if inscricao.data_nascimento
                else ""
            ),
            inscricao.curso.titulo if inscricao.curso else "",
            inscricao.turma.nome if inscricao.turma else "",
            inscricao.situacao,
            (
                inscricao.criado_em.strftime("%d/%m/%Y %H:%M")
                if inscricao.criado_em
                else ""
            ),
            inscricao.observacoes or "",
        ]
        aba.append(linha)
        for indice, valor in enumerate(linha, start=1):
            if isinstance(valor, str) and valor.startswith(PREFIXOS_FORMULA):
                aba.cell(row=aba.max_row, column=indice).data_type = "s"

    for indice, largura in enumerate(LARGURAS, start=1):
        aba.column_dimensions[get_column_letter(indice)].width = largura
    aba.freeze_panes = "A2"
    aba.auto_filter.ref = aba.dimensions

    arquivo = BytesIO()
    planilha.save(arquivo)
    return arquivo.getvalue()
