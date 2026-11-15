"""Serviço do módulo de pré-inscrições (implementa InscricaoService).

O curso precisa existir, estar ativo e ser gratuito; os dados são validados; o
CPF, quando informado, não pode repetir no mesmo curso; a inscrição nasce com
StatusInscricao.RECEBIDA. Não há controle automático de vagas.
"""

from __future__ import annotations

import logging
from typing import Mapping, Sequence

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.extensions import db
from app.models import Curso, Inscricao, StatusInscricao
from app.services.validacao import validar_dados_inscricao

logger = logging.getLogger(__name__)


class InscricaoError(Exception):
    """Erro base do módulo de inscrições."""


class CursoNaoEncontrado(InscricaoError):
    """O curso informado não existe."""


class CursoIndisponivel(InscricaoError):
    """O curso existe, mas não aceita pré-inscrição (pago ou arquivado)."""


class DadosInvalidos(InscricaoError):
    """Falha de validação; erros mapeia campo -> mensagem."""

    def __init__(self, erros: Mapping[str, str]):
        super().__init__("Dados da pré-inscrição inválidos.")
        self.erros = dict(erros)


class CpfDuplicado(InscricaoError):
    """Já existe pré-inscrição com este CPF no curso."""

    mensagem = "Já existe uma pré-inscrição com este CPF neste curso."


class ErroDePersistencia(InscricaoError):
    """Falha ao gravar no banco de dados."""


def obter_curso_para_inscricao(curso_id: int) -> Curso:
    """Retorna o curso se ele existir, estiver ativo e for gratuito."""
    curso = db.session.get(Curso, curso_id)
    if curso is None:
        raise CursoNaoEncontrado(f"Curso {curso_id} não encontrado.")
    if not curso.ativo:
        raise CursoIndisponivel(
            "Este curso não está mais disponível para pré-inscrição."
        )
    if curso.e_pago:
        raise CursoIndisponivel(
            "Este curso é pago e não aceita pré-inscrição. "
            "Use o link de compra na página do curso."
        )
    if not curso.aceita_pre_inscricao:
        raise CursoIndisponivel("Este curso não aceita pré-inscrição.")
    return curso


def cpf_ja_inscrito(curso_id: int, cpf: str | None) -> bool:
    if not cpf:
        return False
    existente = db.session.scalar(
        select(Inscricao.id).where(Inscricao.curso_id == curso_id, Inscricao.cpf == cpf)
    )
    return existente is not None


def gerar_protocolo(inscricao: Inscricao) -> str:
    return f"PRE-{inscricao.id:06d}"


class InscricaoServiceImpl:
    """Implementação concreta de app.contracts.InscricaoService."""

    def criar_pre_inscricao(
        self, curso_id: int, dados: Mapping[str, object]
    ) -> Inscricao:
        curso = obter_curso_para_inscricao(curso_id)

        limpos, erros = validar_dados_inscricao(dados)

        cpf = limpos.get("cpf")
        if "cpf" not in erros and cpf_ja_inscrito(curso.id, cpf):
            erros["cpf"] = CpfDuplicado.mensagem
        if erros:
            raise DadosInvalidos(erros)

        inscricao = Inscricao(
            curso_id=curso.id,
            nome_completo=limpos["nome_completo"],
            cpf=cpf,
            email=limpos["email"],
            telefone=limpos["telefone"],
            data_nascimento=limpos["data_nascimento"],
            observacoes=limpos["observacoes"],
            status=StatusInscricao.RECEBIDA,
        )

        try:
            db.session.add(inscricao)
            db.session.commit()
        except IntegrityError:
            # Envios simultâneos: a restrição única (curso_id, cpf) é a garantia final.
            db.session.rollback()
            if cpf and cpf_ja_inscrito(curso.id, cpf):
                raise DadosInvalidos({"cpf": CpfDuplicado.mensagem}) from None
            logger.exception("Violação de integridade ao salvar pré-inscrição")
            raise ErroDePersistencia(
                "Não foi possível salvar a pré-inscrição."
            ) from None
        except SQLAlchemyError:
            db.session.rollback()
            logger.exception("Erro de banco ao salvar pré-inscrição")
            raise ErroDePersistencia(
                "Não foi possível salvar a pré-inscrição."
            ) from None

        return inscricao

    def listar_inscricoes(
        self,
        curso_id: int | None = None,
        status: StatusInscricao | None = None,
    ) -> Sequence[Inscricao]:
        consulta = select(Inscricao).order_by(Inscricao.criado_em.desc(), Inscricao.id.desc())
        if curso_id is not None:
            consulta = consulta.where(Inscricao.curso_id == curso_id)
        if status is not None:
            consulta = consulta.where(Inscricao.status == status)
        return db.session.scalars(consulta).all()

    def alterar_status(
        self,
        inscricao_id: int,
        status: StatusInscricao,
        administrador_id: int,
    ) -> Inscricao:
        inscricao = db.session.get(Inscricao, inscricao_id)
        if inscricao is None:
            raise InscricaoError(f"Inscrição {inscricao_id} não encontrada.")
        inscricao.status = status
        inscricao.administrador_id = administrador_id
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            logger.exception("Erro de banco ao alterar status da inscrição")
            raise ErroDePersistencia("Não foi possível alterar o status.") from None
        return inscricao


inscricao_service = InscricaoServiceImpl()