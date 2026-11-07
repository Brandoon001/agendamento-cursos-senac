"""Pontos de integração do módulo de catálogo.

Implementação esperada:

- ``listar``: consultar somente cursos ativos usando ``Curso`` e/ou
  ``CatalogoService``.
- ``detalhe``: carregar um curso pelo identificador.
- Cursos pagos devem direcionar o visitante para ``curso.link_externo``.
- Cursos gratuitos devem exibir o CTA para ``inscricoes.pre_inscricao``.

As rotas abaixo são apenas placeholders da fundação e não consultam o banco.
"""

from __future__ import annotations

from flask import render_template

from app.blueprints.catalogo import bp


@bp.get("/")
def listar():
    """Lista pública de cursos. Contrato: responder em ``catalogo.listar``."""
    return render_template("catalogo/lista_cursos.html")


@bp.get("/<int:curso_id>")
def detalhe(curso_id: int):
    """Detalhe público de um curso. Contrato: responder em ``catalogo.detalhe``."""
    return render_template("catalogo/detalhe_curso.html", curso_id=curso_id)
