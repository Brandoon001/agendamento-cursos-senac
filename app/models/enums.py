"""Enumerações de domínio compartilhadas entre os módulos."""

from __future__ import annotations

from enum import Enum


class TipoCurso(str, Enum):
    """Define como o curso é ofertado ao público."""

    PAGO = "pago"
    GRATUITO = "gratuito"


class StatusInscricao(str, Enum):
    """Estados possíveis de uma pré-inscrição.

    Fluxo esperado: recebida -> em análise -> contatada -> finalizada.
    Uma inscrição pode ser cancelada a qualquer momento.
    """

    RECEBIDA = "recebida"
    EM_ANALISE = "em_analise"
    CONTATADA = "contatada"
    FINALIZADA = "finalizada"
    CANCELADA = "cancelada"
