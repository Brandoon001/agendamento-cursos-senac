"""Regras de negócio do módulo de cursos e turmas."""

from __future__ import annotations

import re
import unicodedata
from datetime import date, time
from decimal import Decimal, InvalidOperation
from typing import Iterable, Mapping
from urllib.parse import urlparse

from sqlalchemy import or_

from app.extensions import db
from app.models import Curso, Turma
from app.models.enums import TipoCurso

CAMPOS_CURSO = (
    "titulo",
    "slug",
    "descricao",
    "tipo",
    "link_externo",
    "valor",
    "carga_horaria",
    "data_inicio",
    "data_fim",
    "vagas",
    "imagem_url",
    "ativo",
)

CAMPOS_TURMA = (
    "nome",
    "dias_semana",
    "hora_inicio",
    "hora_fim",
    "data_inicio",
    "data_fim",
    "vagas",
    "ativo",
)


def gerar_slug(texto: str) -> str:
    """Converte um texto livre em um identificador amigável para URL."""
    normalizado = unicodedata.normalize("NFKD", texto or "")
    sem_acentos = normalizado.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", sem_acentos).strip("-").lower()
    return slug or "curso"


class CursoService:
    """Operações de consulta e manutenção de cursos e turmas."""

    def listar_cursos_publicos(
        self,
        termo: str | None = None,
        tipo: str | TipoCurso | None = None,
    ) -> list[Curso]:
        """Lista somente cursos ativos, com busca e filtro opcionais."""
        consulta = db.select(Curso).where(Curso.ativo.is_(True))

        if termo:
            busca = f"%{termo.strip()}%"
            consulta = consulta.where(
                or_(
                    Curso.titulo.ilike(busca),
                    Curso.descricao.ilike(busca),
                )
            )

        tipo_normalizado = self._normalizar_tipo(tipo)
        if tipo_normalizado is not None:
            consulta = consulta.where(Curso.tipo == tipo_normalizado)

        consulta = consulta.order_by(Curso.titulo.asc())
        return list(db.session.scalars(consulta).all())

    def listar_todos(
        self,
        termo: str | None = None,
        situacao: str | None = None,
    ) -> list[Curso]:
        """Lista cursos para o painel administrativo, ativos e inativos."""
        consulta = db.select(Curso)

        if termo:
            busca = f"%{termo.strip()}%"
            consulta = consulta.where(
                or_(
                    Curso.titulo.ilike(busca),
                    Curso.descricao.ilike(busca),
                )
            )

        if situacao == "ativo":
            consulta = consulta.where(Curso.ativo.is_(True))
        elif situacao == "inativo":
            consulta = consulta.where(Curso.ativo.is_(False))

        consulta = consulta.order_by(Curso.titulo.asc())
        return list(db.session.scalars(consulta).all())

    def obter_curso(self, curso_id: int) -> Curso | None:
        return db.session.get(Curso, curso_id)

    def obter_link_compra(self, curso: Curso) -> str:
        if not curso.e_pago:
            raise ValueError("Somente cursos pagos possuem link de compra.")
        if not curso.link_externo:
            raise ValueError("O curso pago não possui link externo cadastrado.")
        return curso.link_externo

    def criar_curso(self, dados: Mapping[str, object]) -> Curso:
        curso = Curso()
        self._aplicar_dados_do_curso(curso, dados, criando=True)
        db.session.add(curso)
        self._salvar("Não foi possível cadastrar o curso.")
        return curso

    def atualizar_curso(
        self,
        curso: Curso,
        dados: Mapping[str, object],
    ) -> Curso:
        self._aplicar_dados_do_curso(curso, dados, criando=False)
        self._salvar("Não foi possível salvar o curso.")
        return curso

    def definir_situacao(self, curso: Curso, ativo: bool) -> Curso:
        curso.ativo = ativo
        self._salvar("Não foi possível alterar a situação do curso.")
        return curso

    def excluir_curso(self, curso: Curso) -> None:
        if curso.inscricoes:
            raise ValueError(
                "Este curso possui inscrições e não pode ser excluído. "
                "Desative-o para preservar o histórico."
            )

        db.session.delete(curso)
        try:
            db.session.commit()
        except Exception as erro:  # pragma: no cover - proteção do banco
            db.session.rollback()
            raise ValueError(
                "Não foi possível excluir o curso. Desative-o para arquivar."
            ) from erro

    def listar_turmas(
        self,
        curso_id: int,
        apenas_ativas: bool = False,
    ) -> list[Turma]:
        consulta = db.select(Turma).where(Turma.curso_id == curso_id)
        if apenas_ativas:
            consulta = consulta.where(Turma.ativo.is_(True))
        consulta = consulta.order_by(Turma.nome.asc())
        return list(db.session.scalars(consulta).all())

    def listar_turmas_disponiveis(self, curso_id: int) -> list[Turma]:
        """Turmas ativas, de curso ativo e com vagas livres para o público."""
        return [
            turma
            for turma in self.listar_turmas(curso_id, apenas_ativas=True)
            if turma.disponivel
        ]

    def obter_turma(self, turma_id: int) -> Turma | None:
        return db.session.get(Turma, turma_id)

    def criar_turma(
        self,
        curso_id: int,
        dados: Mapping[str, object],
    ) -> Turma:
        curso = self.obter_curso(curso_id)
        if curso is None:
            raise ValueError("Curso não encontrado.")

        turma = Turma(curso=curso)
        self._aplicar_dados_da_turma(turma, dados)
        db.session.add(turma)
        self._salvar("Não foi possível cadastrar a turma.")
        return turma

    def atualizar_turma(
        self,
        turma: Turma,
        dados: Mapping[str, object],
    ) -> Turma:
        self._aplicar_dados_da_turma(turma, dados)
        self._salvar("Não foi possível salvar a turma.")
        return turma

    def definir_situacao_turma(self, turma: Turma, ativo: bool) -> Turma:
        turma.ativo = ativo
        self._salvar("Não foi possível alterar a situação da turma.")
        return turma

    def excluir_turma(self, turma: Turma) -> None:
        if turma.inscricoes:
            raise ValueError(
                "Esta turma possui inscrições e não pode ser excluída. "
                "Desative-a para preservar o histórico."
            )

        db.session.delete(turma)
        try:
            db.session.commit()
        except Exception as erro:  # pragma: no cover - proteção do banco
            db.session.rollback()
            raise ValueError(
                "Não foi possível excluir a turma. Desative-a para arquivar."
            ) from erro

    def _aplicar_dados_do_curso(
        self,
        curso: Curso,
        dados: Mapping[str, object],
        *,
        criando: bool,
    ) -> None:
        tipo = self._normalizar_tipo(dados.get("tipo"))
        if tipo is None:
            raise ValueError("Selecione o tipo do curso.")

        titulo = self._texto(dados.get("titulo"))
        if not titulo:
            raise ValueError("Informe o nome do curso.")

        descricao = self._texto(dados.get("descricao"))
        if not descricao:
            raise ValueError("Informe a descrição do curso.")

        link_externo = self._texto(dados.get("link_externo"))
        slug_informado = self._texto(dados.get("slug"))

        if tipo is TipoCurso.PAGO and not link_externo:
            raise ValueError("Cursos pagos precisam de um link externo.")
        if tipo is TipoCurso.PAGO:
            link_externo = self._validar_link_externo(link_externo)
        if tipo is TipoCurso.GRATUITO:
            link_externo = None
            curso.valor = None

        carga_horaria = self._inteiro(dados.get("carga_horaria"))
        vagas = self._inteiro(dados.get("vagas"))
        data_inicio = self._data(dados.get("data_inicio"))
        data_fim = self._data(dados.get("data_fim"))

        if carga_horaria is not None and carga_horaria <= 0:
            raise ValueError("A carga horária deve ser maior que zero.")
        if vagas is not None and vagas < 0:
            raise ValueError("A quantidade de vagas não pode ser negativa.")
        if data_inicio and data_fim and data_fim < data_inicio:
            raise ValueError(
                "A data de término não pode ser anterior à data de início."
            )

        valor = None
        if tipo is TipoCurso.PAGO:
            valor = self._decimal(dados.get("valor"))
            if valor is not None and valor < 0:
                raise ValueError("O valor do curso não pode ser negativo.")

        curso.titulo = titulo
        curso.descricao = descricao
        curso.tipo = tipo
        curso.link_externo = link_externo
        curso.valor = valor
        curso.carga_horaria = carga_horaria
        curso.data_inicio = data_inicio
        curso.data_fim = data_fim
        curso.vagas = vagas
        curso.imagem_url = self._texto(dados.get("imagem_url"))
        curso.ativo = self._booleano(dados.get("ativo"), padrao=True)

        base_slug = slug_informado or gerar_slug(titulo)
        curso.slug = self._slug_unico(
            gerar_slug(base_slug),
            curso_id=None if criando else curso.id,
        )

    def _aplicar_dados_da_turma(
        self,
        turma: Turma,
        dados: Mapping[str, object],
    ) -> None:
        nome = self._texto(dados.get("nome"))
        if not nome:
            raise ValueError("Informe o nome ou código da turma.")

        hora_inicio = self._hora(dados.get("hora_inicio"))
        hora_fim = self._hora(dados.get("hora_fim"))
        data_inicio = self._data(dados.get("data_inicio"))
        data_fim = self._data(dados.get("data_fim"))
        vagas = self._inteiro(dados.get("vagas"))

        if (hora_inicio is None) != (hora_fim is None):
            raise ValueError("Informe o horário de início e de término.")
        if hora_inicio and hora_fim and hora_fim <= hora_inicio:
            raise ValueError(
                "O horário de término deve ser posterior ao de início."
            )
        if data_inicio and data_fim and data_fim < data_inicio:
            raise ValueError(
                "A data de término não pode ser anterior à data de início."
            )
        if vagas is not None and vagas < 0:
            raise ValueError("A quantidade de vagas não pode ser negativa.")

        turma.nome = nome
        turma.dias_semana = self._texto(dados.get("dias_semana"))
        turma.hora_inicio = hora_inicio
        turma.hora_fim = hora_fim
        turma.data_inicio = data_inicio
        turma.data_fim = data_fim
        turma.vagas = vagas
        turma.ativo = self._booleano(dados.get("ativo"), padrao=True)

    def _slug_unico(self, base: str, curso_id: int | None = None) -> str:
        slug = base or "curso"
        contador = 2
        while True:
            consulta = db.select(Curso).where(Curso.slug == slug)
            if curso_id is not None:
                consulta = consulta.where(Curso.id != curso_id)
            if db.session.scalar(consulta) is None:
                return slug
            slug = f"{base}-{contador}"
            contador += 1

    @staticmethod
    def _salvar(mensagem: str) -> None:
        try:
            db.session.commit()
        except Exception as erro:
            db.session.rollback()
            raise ValueError(mensagem) from erro

    @staticmethod
    def _normalizar_tipo(
        valor: str | TipoCurso | None,
    ) -> TipoCurso | None:
        if valor is None or valor == "":
            return None
        if isinstance(valor, TipoCurso):
            return valor
        try:
            return TipoCurso(str(valor).strip().lower())
        except ValueError:
            return None

    @staticmethod
    def _texto(valor: object) -> str:
        if valor is None:
            return ""
        return str(valor).strip()

    @staticmethod
    def _booleano(valor: object, *, padrao: bool) -> bool:
        if valor is None:
            return padrao
        if isinstance(valor, bool):
            return valor
        if isinstance(valor, str):
            return valor.strip().lower() not in {
                "",
                "0",
                "false",
                "nao",
                "não",
                "off",
            }
        return bool(valor)

    @staticmethod
    def _inteiro(valor: object) -> int | None:
        if valor is None or valor == "":
            return None
        try:
            return int(valor)
        except (TypeError, ValueError) as erro:
            raise ValueError(
                "Informe um número inteiro válido."
            ) from erro

    @staticmethod
    def _decimal(valor: object) -> Decimal | None:
        if valor is None or valor == "":
            return None
        if isinstance(valor, Decimal):
            return valor
        try:
            return Decimal(str(valor))
        except (InvalidOperation, TypeError, ValueError) as erro:
            raise ValueError("Informe um valor numérico válido.") from erro

    @staticmethod
    def _data(valor: object) -> date | None:
        if valor is None or valor == "":
            return None
        if isinstance(valor, date):
            return valor
        try:
            return date.fromisoformat(str(valor))
        except ValueError as erro:
            raise ValueError(
                "Informe uma data válida (AAAA-MM-DD)."
            ) from erro

    @staticmethod
    def _hora(valor: object) -> time | None:
        if valor is None or valor == "":
            return None
        if isinstance(valor, time):
            return valor
        try:
            return time.fromisoformat(str(valor))
        except ValueError as erro:
            raise ValueError(
                "Informe um horário válido (HH:MM)."
            ) from erro

    @staticmethod
    def _validar_link_externo(link: str) -> str:
        endereco = urlparse(link)
        if endereco.scheme not in {"http", "https"} or not endereco.netloc:
            raise ValueError(
                "Informe um link externo válido, iniciado por http:// ou "
                "https://."
            )
        return link


def curso_esta_visivel(curso: Curso | None) -> bool:
    """Atalho usado pelas rotas públicas."""
    return curso is not None and curso.ativo is not False


def contar_por_tipo(cursos: Iterable[Curso]) -> dict[str, int]:
    """Retorna a quantidade de cursos por tipo."""
    contagem = {tipo.value: 0 for tipo in TipoCurso}
    for curso in cursos:
        contagem[curso.tipo.value] = contagem.get(curso.tipo.value, 0) + 1
    return contagem
