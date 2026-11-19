"""Regras de negócio e persistência das pré-inscrições."""

from __future__ import annotations

from typing import Mapping
import re

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.extensions import db
from app.models import Curso, Inscricao, StatusInscricao


class ErroPreInscricao(Exception):
    """Erro esperado de regra de negócio da pré-inscrição."""


class CursoIndisponivel(ErroPreInscricao):
    """Curso inexistente, pago ou arquivado."""


class CpfDuplicado(ErroPreInscricao):
    """CPF já utilizado em outra pré-inscrição do mesmo curso."""


class FalhaPersistencia(ErroPreInscricao):
    """Falha inesperada ao salvar a pré-inscrição."""


class InscricaoService:

    @staticmethod
    def _normalizar_cpf(valor: object) -> str | None:
        numeros = re.sub(r"\D", "", str(valor or ""))
        return numeros or None

    @staticmethod
    def _normalizar_telefone(valor: object) -> str:
        return re.sub(r"\D", "", str(valor or ""))

    def criar_pre_inscricao(
        self,
        curso_id: int,
        dados: Mapping[str, object],
    ) -> Inscricao:

        curso = db.session.get(Curso, curso_id)

        if curso is None or not curso.aceita_pre_inscricao:
            raise CursoIndisponivel(
                "Este curso não está disponível para pré-inscrição."
            )

        cpf = self._normalizar_cpf(dados.get("cpf"))

        if cpf and db.session.query(Inscricao.id).filter_by(
            curso_id=curso_id,
            cpf=cpf,
        ).first():

            raise CpfDuplicado(
                "Já existe uma pré-inscrição com este CPF para o curso selecionado."
            )

        try:
            inscricao = Inscricao(
                curso=curso,
                nome_completo=str(dados["nome_completo"]).strip(),
                cpf=cpf,
                email=str(dados["email"]).strip().lower(),
                telefone=self._normalizar_telefone(dados["telefone"]),
                data_nascimento=dados["data_nascimento"],
                observacoes=(
                    str(dados.get("observacoes") or "").strip() or None
                ),
                status=StatusInscricao.RECEBIDA,
            )

            db.session.add(inscricao)
            db.session.commit()

            return inscricao

        except IntegrityError as erro:
            db.session.rollback()

            if cpf:
                duplicada = db.session.query(Inscricao.id).filter_by(
                    curso_id=curso_id,
                    cpf=cpf,
                ).first()

                if duplicada:
                    raise CpfDuplicado(
                        "Já existe uma pré-inscrição com este CPF para o curso selecionado."
                    ) from erro

            raise FalhaPersistencia(
                "Não foi possível registrar a pré-inscrição."
            ) from erro

        except (SQLAlchemyError, KeyError, TypeError, ValueError) as erro:
            db.session.rollback()

            raise FalhaPersistencia(
                "Ocorreu um erro ao registrar a pré-inscrição. Tente novamente."
            ) from erro

    def listar_inscricoes(
        self,
        curso_id: int | None = None,
        status: StatusInscricao | None = None,
    ) -> list[Inscricao]:

        consulta = Inscricao.query

        if curso_id is not None:
            consulta = consulta.filter_by(curso_id=curso_id)

        if status is not None:
            consulta = consulta.filter_by(status=status)

        return consulta.order_by(Inscricao.criado_em.desc()).all()

    def alterar_status(
        self,
        inscricao_id: int,
        status: StatusInscricao,
        administrador_id: int,
    ) -> Inscricao:

        from app.models import Administrador

        inscricao = db.session.get(Inscricao, inscricao_id)
        administrador = db.session.get(
            Administrador,
            administrador_id,
        )

        if inscricao is None:
            raise ErroPreInscricao("Pré-inscrição não encontrada.")

        if administrador is None or not administrador.ativo:
            raise ErroPreInscricao(
                "Administrador não encontrado ou inativo."
            )

        try:
            inscricao.status = status
            inscricao.administrador_id = administrador_id

            db.session.commit()

            return inscricao

        except SQLAlchemyError as erro:
            db.session.rollback()

            raise FalhaPersistencia(
                "Não foi possível atualizar a situação da pré-inscrição."
            ) from erro


inscricao_service = InscricaoService()