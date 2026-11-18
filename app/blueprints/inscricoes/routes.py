"""Rotas públicas de pré-inscrição em cursos gratuitos."""

from __future__ import annotations

from flask import (
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user

from app.blueprints.inscricoes import bp
from app.extensions import db
from app.forms.inscricao import InscricaoForm, formatar_cpf
from app.models import Inscricao, Turma
from app.services.curso_service import CursoService
from app.services.inscricao_service import InscricaoService


@bp.route("/<int:curso_id>/pre-inscricao", methods=["GET", "POST"])
def pre_inscricao(curso_id: int):
    """Exibe e processa o formulário de pré-inscrição do curso gratuito."""
    curso = CursoService().obter_curso(curso_id)
    if curso is None or not curso.aceita_pre_inscricao:
        abort(404)

    turma_id = _turma_id_da_requisicao()
    turma = None
    if turma_id is not None:
        turma = db.session.get(Turma, turma_id)
        if turma is None or turma.curso_id != curso_id or turma.ativo is False:
            abort(404)
        if not turma.disponivel:
            flash("Esta turma não possui vagas disponíveis no momento.", "warning")

    formulario = InscricaoForm()
    if request.method == "GET":
        formulario.turma_id.data = str(turma_id) if turma_id else ""

    if formulario.validate_on_submit():
        dados = {
            "nome_completo": formulario.nome_completo.data,
            "cpf": formatar_cpf(formulario.cpf.data),
            "email": formulario.email.data,
            "telefone": formulario.telefone.data,
            "data_nascimento": formulario.data_nascimento.data,
            "observacoes": formulario.observacoes.data,
        }
        try:
            inscricao = InscricaoService().criar_pre_inscricao(
                curso_id,
                dados,
                turma_id,
            )
        except ValueError as erro:
            flash(str(erro), "error")
        else:
            session["ultima_inscricao_id"] = inscricao.id
            flash("Pré-inscrição registrada com sucesso!", "success")
            return redirect(
                url_for("inscricoes.confirmacao", inscricao_id=inscricao.id)
            )

    return render_template(
        "inscricoes/pre_inscricao.html",
        formulario=formulario,
        curso=curso,
        turma=turma,
    )


@bp.get("/<int:inscricao_id>/confirmacao")
def confirmacao(inscricao_id: int):
    """Mostra o comprovante apenas ao candidato desta sessão ou ao admin."""
    inscricao = db.session.get(Inscricao, inscricao_id)
    if inscricao is None:
        abort(404)
    if (
        not current_user.is_authenticated
        and session.get("ultima_inscricao_id") != inscricao.id
    ):
        abort(404)

    return render_template(
        "inscricoes/confirmacao.html",
        inscricao=inscricao,
    )


def _turma_id_da_requisicao() -> int | None:
    valor = request.form.get("turma_id") or request.args.get("turma_id")
    return int(valor) if valor and str(valor).isdigit() else None
