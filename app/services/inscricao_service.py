"""Regras de negócio das pré-inscrições em cursos gratuitos."""

from __future__ import annotations

from typing import Mapping

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import Curso, Inscricao, Turma
from app.models.enums import StatusInscricao


class InscricaoService:
    """Cria, consulta e atualiza pré-inscrições."""

    def criar_pre_inscricao(
        self,
        curso_id: int,
        dados: Mapping[str, object],
        turma_id: int | None = None,
    ) -> Inscricao:
        """Persiste uma inscrição RECEBIDA após validar curso, turma e CPF."""
        curso = db.session.get(Curso, curso_id)
        if curso is None or not curso.aceita_pre_inscricao:
            raise ValueError("Este curso não aceita pré-inscrições no momento.")

        turma = None
        if turma_id is not None:
            turma = db.session.get(Turma, turma_id)
            if turma is None or turma.curso_id != curso_id or turma.ativo is False:
                raise ValueError("A turma selecionada não está disponível.")
            if not turma.tem_vagas:
                raise ValueError("Não há vagas disponíveis nesta turma.")

        cpf = dados.get("cpf") or None
        if cpf and self._cpf_ja_inscrito(curso_id, str(cpf)):
            raise ValueError("Já existe uma pré-inscrição com este CPF no curso.")

        inscricao = Inscricao(
            curso_id=curso_id,
            turma_id=turma.id if turma else None,
            nome_completo=str(dados.get("nome_completo", "")).strip(),
            cpf=cpf,
            email=dados.get("email") or None,
            telefone=dados.get("telefone") or None,
            data_nascimento=dados.get("data_nascimento"),
            observacoes=dados.get("observacoes") or None,
            status=StatusInscricao.RECEBIDA,
        )

        db.session.add(inscricao)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ValueError(
                "Já existe uma pré-inscrição com este CPF no curso."
            ) from None
        return inscricao

    def listar_inscricoes(
        self,
        curso_id: int | None = None,
        status: StatusInscricao | str | None = None,
        termo: str | None = None,
    ) -> list[Inscricao]:
        """Lista inscrições com curso/turma carregados, da mais recente à mais antiga."""
        consulta = db.select(Inscricao).options(
            joinedload(Inscricao.curso),
            joinedload(Inscricao.turma),
        )

        if curso_id is not None:
            consulta = consulta.where(Inscricao.curso_id == curso_id)
        if status:
            status_enum = self._converter_status(status)
            if status_enum is not None:
                consulta = consulta.where(Inscricao.status == status_enum)
        if termo:
            padrao = f"%{termo.strip().replace('%', '\\%').replace('_', '\\_')}%"
            consulta = consulta.where(
                or_(
                    Inscricao.nome_completo.ilike(padrao, escape="\\"),
                    Inscricao.cpf.ilike(padrao, escape="\\"),
                    Inscricao.email.ilike(padrao, escape="\\"),
                )
            )

        return list(
            db.session.scalars(
                consulta.order_by(Inscricao.criado_em.desc(), Inscricao.id.desc())
            )
        )

    def alterar_status(
        self,
        inscricao_id: int,
        status: StatusInscricao | str,
        administrador_id: int,
    ) -> Inscricao:
        """Atualiza a situação da inscrição e registra quem a alterou."""
        inscricao = db.session.get(Inscricao, inscricao_id)
        if inscricao is None:
            raise ValueError("Inscrição não encontrada.")

        status_enum = self._converter_status(status)
        if status_enum is None:
            raise ValueError("Situação inválida.")

        inscricao.status = status_enum
        inscricao.administrador_id = administrador_id
        db.session.commit()
        return inscricao

    def contar_por_status(self) -> dict[StatusInscricao, int]:
        """Quantidade de inscrições em cada situação."""
        linhas = db.session.execute(
            db.select(Inscricao.status, db.func.count()).group_by(Inscricao.status)
        ).all()
        return {status: total for status, total in linhas}

    def _cpf_ja_inscrito(self, curso_id: int, cpf: str) -> bool:
        consulta = db.select(db.func.count()).where(
            Inscricao.curso_id == curso_id,
            Inscricao.cpf == cpf,
        )
        return bool(db.session.scalar(consulta))

    @staticmethod
    def _converter_status(status: StatusInscricao | str) -> StatusInscricao | None:
        if isinstance(status, StatusInscricao):
            return status
        try:
            return StatusInscricao(str(status).strip())
        except ValueError:
            return None
