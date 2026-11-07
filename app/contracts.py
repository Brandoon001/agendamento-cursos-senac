"""Contratos públicos entre os módulos do sistema.

Este arquivo descreve as operações que cada módulo deve oferecer aos demais.
As implementações concretas ficam a cargo de cada integrante, preferencialmente
em ``app/services``. Os contratos evitam que um módulo dependa dos detalhes
internos do outro.

Cursos com inscrições não devem ser excluídos: o histórico é preservado e o
banco bloqueia a exclusão. Nesses casos, o curso deve ser arquivado por meio de
``Curso.ativo = False``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Mapping, Protocol, Sequence

if TYPE_CHECKING:
    from app.models import Administrador, Curso, Inscricao
    from app.models.enums import StatusInscricao


class CatalogoService(Protocol):
    """Operações esperadas do módulo de catálogo."""

    def listar_cursos_publicos(self) -> Sequence[Curso]:
        """Lista somente cursos ativos e visíveis ao público."""

    def obter_curso(self, curso_id: int) -> Curso | None:
        """Busca um curso pelo identificador."""

    def obter_link_compra(self, curso: Curso) -> str:
        """Retorna o link externo de compra de um curso pago."""


class InscricaoService(Protocol):
    """Operações esperadas do módulo de pré-inscrições.

    O contrato não pressupõe controle automático de vagas, lista de espera ou
    reserva. Essas regras só devem existir se forem definidas explicitamente.
    """

    def criar_pre_inscricao(
        self,
        curso_id: int,
        dados: Mapping[str, object],
    ) -> Inscricao:
        """Cria uma inscrição apenas para curso gratuito e ativo.

        Não há controle automático de vagas nesta camada. Eventuais regras de
        disponibilidade, lista de espera ou limites pertencem ao módulo de
        inscrições e devem ser definidas explicitamente antes de serem
        aplicadas.
        """

    def listar_inscricoes(
        self,
        curso_id: int | None = None,
        status: StatusInscricao | None = None,
    ) -> Sequence[Inscricao]:
        """Lista inscrições, opcionalmente filtradas por curso e situação."""

    def alterar_status(
        self,
        inscricao_id: int,
        status: StatusInscricao,
        administrador_id: int,
    ) -> Inscricao:
        """Atualiza a situação de uma inscrição e registra o responsável."""


class AutenticacaoService(Protocol):
    """Operações esperadas do módulo administrativo/autenticação."""

    def autenticar(self, email: str, senha: str) -> Administrador | None:
        """Retorna o administrador ativo quando as credenciais são válidas."""
