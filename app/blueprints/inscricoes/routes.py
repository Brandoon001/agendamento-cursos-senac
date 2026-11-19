"""Rotas públicas do fluxo de pré-inscrição."""

from __future__ import annotations

from flask import (
    abort,
    flash,
    redirect,
    render_template,
    url_for,
)

from app.blueprints.inscricoes import bp
from app.extensions import db
from app.forms.inscricao import PreInscricaoForm
from app.models import Curso, Inscricao

from app.services.inscricao_service import (
    CpfDuplicado,
    CursoIndisponivel,
    ErroPreInscricao,
    inscricao_service,
)


@bp.route("/<int:curso_id>/pre-inscricao", methods=["GET", "POST"])
def pre_inscricao(curso_id: int):

    curso = db.session.get(Curso, curso_id)

    if curso is None:
        abort(404)

    if not curso.aceita_pre_inscricao:
        flash(
            "Este curso não está disponível para pré-inscrição.",
            "warning",
        )
        return redirect(url_for("catalogo.listar"))

    form = PreInscricaoForm()

    if form.validate_on_submit():

        dados = {
            "nome_completo": form.nome_completo.data,
            "cpf": form.cpf.data,
            "email": form.email.data,
            "telefone": form.telefone.data,
            "data_nascimento": form.data_nascimento.data,
            "observacoes": form.observacoes.data,
        }

        try:
            inscricao = inscricao_service.criar_pre_inscricao(
                curso_id,
                dados,
            )

        except CpfDuplicado as erro:
            form.cpf.errors.append(str(erro))

        except CursoIndisponivel as erro:
            flash(str(erro), "warning")
            return redirect(url_for("catalogo.listar"))

        except ErroPreInscricao:
            flash(
                "Não foi possível registrar sua pré-inscrição. Tente novamente.",
                "error",
            )

        else:
            flash(
                "Pré-inscrição enviada com sucesso!",
                "success",
            )

            return redirect(
                url_for(
                    "inscricoes.confirmacao",
                    inscricao_id=inscricao.id,
                )
            )

    return render_template(
        "inscricoes/pre_inscricao.html",
        form=form,
        curso=curso,
    )


@bp.get("/<int:inscricao_id>/confirmacao")
def confirmacao(inscricao_id: int):

    inscricao = db.session.get(Inscricao, inscricao_id)

    if inscricao is None:
        abort(404)

    return render_template(
        "inscricoes/confirmacao.html",
        inscricao=inscricao,
    )