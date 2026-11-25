"""Modelos e enumerações compartilhados da aplicação."""

from app.models.administrador import Administrador
from app.models.curso import Curso
from app.models.enums import StatusInscricao, TipoCurso
from app.models.inscricao import Inscricao
from app.models.turma import Turma

__all__ = [
    "Administrador",
    "Curso",
    "Inscricao",
    "StatusInscricao",
    "TipoCurso",
    "Turma",
]
