"""Pontos de integração do módulo de pré-inscrições.

Implementação esperada:

- ``pre_inscricao`` (GET): exibir o formulário somente para curso gratuito,
  ativo e que aceite inscrições.
- ``pre_inscricao`` (POST): validar CSRF, validar os dados, impedir duplicidade
  de CPF quando informado e persistir ``Inscricao`` via ``InscricaoService``.
- ``confirmacao``: exibir o comprovante/protocolo após a criação.
- A inscrição deve nascer com ``StatusInscricao.RECEBIDA``.
- CPF, e-mail e telefone são opcionais no modelo; a obrigatoriedade deve ser
  definida pela validação deste módulo.
- Não implemente controle automático de vagas sem uma regra explícita.
- Nunca armazenar dados reais de alunos em fixtures, seeds ou testes.

As rotas abaixo são placeholders e não persistem dados.
"""

from __future__ import annotations

from flask import render_template

from app.blueprints.inscricoes import bp


@bp.route("/<int:curso_id>/pre-inscricao", methods=["GET", "POST"])
def pre_inscricao(curso_id: int):
    """Formulário e envio de pré-inscrição. Contrato: ``inscricoes.pre_inscricao``."""
    return render_template("inscricoes/pre_inscricao.html", curso_id=curso_id)


@bp.get("/<int:inscricao_id>/confirmacao")
def confirmacao(inscricao_id: int):
    """Confirmação da pré-inscrição. Contrato: ``inscricoes.confirmacao``."""
    return render_template("inscricoes/confirmacao.html", inscricao_id=inscricao_id)
