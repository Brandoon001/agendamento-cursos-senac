"""Pontos de integração do painel administrativo.

Todo o Blueprint exige autenticação por meio do ``before_request`` abaixo.
Novas rotas administrativas adicionadas neste arquivo herdam essa proteção.

Implementação esperada:

- ``dashboard``: visão geral de cursos e inscrições.
- CRUD de cursos pagos e gratuitos.
- Cursos com inscrições devem ser arquivados (``ativo = False``), nunca
  excluídos; o banco bloqueia a exclusão para preservar o histórico.
- Análise e alteração de status das pré-inscrições.
"""

from __future__ import annotations

from flask import render_template
from flask_login import login_required

from app.blueprints.admin import bp


@bp.before_request
@login_required
def exigir_autenticacao():
    """Protege todas as rotas administrativas."""


@bp.get("/")
def dashboard():
    """Painel inicial. Contrato: responder em ``admin.dashboard``."""
    return render_template("admin/dashboard.html")
