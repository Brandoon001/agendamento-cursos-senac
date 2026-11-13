"""Rotas do painel administrativo de cursos e turmas."""

from __future__ import annotations

from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.blueprints.admin import bp
from app.extensions import db
from app.forms.curso import CursoForm, TurmaForm
from app.models import Curso, Inscricao, Turma
from app.services.curso_service import (
    CAMPOS_CURSO,
    CAMPOS_TURMA,
    CursoService,
)


@bp.before_request
@login_required
def exigir_autenticacao():
    """Protege todas as rotas administrativas."""


@bp.get("/")
def dashboard():
    """Painel inicial com indicadores do módulo de cursos."""
    servico = CursoService()
    cursos = servico.listar_todos()

    return render_template(
        "admin/dashboard.html",
        total_cursos=len(cursos),
        cursos_ativos=sum(1 for curso in cursos if curso.ativo),
        total_turmas=db.session.scalar(
            db.select(db.func.count()).select_from(Turma)
        ),
        total_inscricoes=db.session.scalar(
            db.select(db.func.count()).select_from(Inscricao)
        ),
        cursos_recentes=sorted(
            cursos,
            key=lambda curso: curso.criado_em,
            reverse=True,
        )[:5],
    )


@bp.get("/cursos")
def cursos():
    """Lista administrativa de cursos, incluindo inativos."""
    termo = request.args.get("q", "").strip()
    situacao = request.args.get("situacao", "").strip() or None
    servico = CursoService()

    return render_template(
        "admin/cursos/lista.html",
        cursos=servico.listar_todos(termo=termo or None, situacao=situacao),
        termo=termo,
        situacao=situacao or "",
    )


@bp.route("/cursos/novo", methods=["GET", "POST"])
def novo_curso():
    """Cadastra um novo curso."""
    formulario = CursoForm()
    servico = CursoService()

    if formulario.validate_on_submit():
        try:
            curso = servico.criar_curso(_dados_do_formulario(formulario))
        except ValueError as erro:
            flash(str(erro), "error")
        else:
            flash("Curso cadastrado com sucesso.", "success")
            return redirect(
                url_for("admin.turmas_do_curso", curso_id=curso.id)
            )

    return render_template(
        "admin/cursos/formulario.html",
        formulario=formulario,
        curso=None,
        titulo_pagina="Novo curso",
    )


@bp.route("/cursos/<int:curso_id>/editar", methods=["GET", "POST"])
def editar_curso(curso_id: int):
    """Edita os dados de um curso existente."""
    servico = CursoService()
    curso = servico.obter_curso(curso_id)
    if curso is None:
        flash("Curso não encontrado.", "error")
        return redirect(url_for("admin.cursos"))

    formulario = CursoForm(obj=curso)

    if request.method == "GET":
        formulario.tipo.data = curso.tipo.value

    if formulario.validate_on_submit():
        try:
            servico.atualizar_curso(curso, _dados_do_formulario(formulario))
        except ValueError as erro:
            flash(str(erro), "error")
        else:
            flash("Curso atualizado com sucesso.", "success")
            return redirect(url_for("admin.cursos"))

    if request.method == "GET" and curso.slug:
        formulario.slug.data = curso.slug

    return render_template(
        "admin/cursos/formulario.html",
        formulario=formulario,
        curso=curso,
        titulo_pagina=f"Editar curso: {curso.titulo}",
    )


@bp.post("/cursos/<int:curso_id>/ativar")
def ativar_curso(curso_id: int):
    """Ativa um curso para exibição pública."""
    servico = CursoService()
    curso = servico.obter_curso(curso_id)
    if curso is None:
        flash("Curso não encontrado.", "error")
    else:
        servico.definir_situacao(curso, True)
        flash("Curso ativado com sucesso.", "success")
    return redirect(_destino_admin("admin.cursos"))


@bp.post("/cursos/<int:curso_id>/desativar")
def desativar_curso(curso_id: int):
    """Desativa um curso sem apagar seu histórico."""
    servico = CursoService()
    curso = servico.obter_curso(curso_id)
    if curso is None:
        flash("Curso não encontrado.", "error")
    else:
        servico.definir_situacao(curso, False)
        flash("Curso desativado com sucesso.", "success")
    return redirect(_destino_admin("admin.cursos"))


@bp.post("/cursos/<int:curso_id>/excluir")
def excluir_curso(curso_id: int):
    """Exclui um curso somente quando não há inscrições vinculadas."""
    servico = CursoService()
    curso = servico.obter_curso(curso_id)
    if curso is None:
        flash("Curso não encontrado.", "error")
        return redirect(url_for("admin.cursos"))

    try:
        servico.excluir_curso(curso)
    except ValueError as erro:
        flash(str(erro), "error")
    else:
        flash("Curso excluído com sucesso.", "success")

    return redirect(url_for("admin.cursos"))


@bp.get("/cursos/<int:curso_id>/turmas")
def turmas_do_curso(curso_id: int):
    """Gerencia as turmas e horários de um curso."""
    servico = CursoService()
    curso = servico.obter_curso(curso_id)
    if curso is None:
        flash("Curso não encontrado.", "error")
        return redirect(url_for("admin.cursos"))

    return render_template(
        "admin/cursos/turmas.html",
        curso=curso,
        turmas=servico.listar_turmas(curso_id),
    )


@bp.route("/cursos/<int:curso_id>/turmas/nova", methods=["GET", "POST"])
def nova_turma(curso_id: int):
    """Cadastra uma turma para o curso."""
    servico = CursoService()
    curso = servico.obter_curso(curso_id)
    if curso is None:
        flash("Curso não encontrado.", "error")
        return redirect(url_for("admin.cursos"))

    formulario = TurmaForm()

    if formulario.validate_on_submit():
        try:
            servico.criar_turma(curso_id, _dados_do_formulario(formulario))
        except ValueError as erro:
            flash(str(erro), "error")
        else:
            flash("Turma cadastrada com sucesso.", "success")
            return redirect(
                url_for("admin.turmas_do_curso", curso_id=curso.id)
            )

    return render_template(
        "admin/cursos/turma_formulario.html",
        formulario=formulario,
        curso=curso,
        turma=None,
        titulo_pagina=f"Nova turma: {curso.titulo}",
    )


@bp.route("/turmas/<int:turma_id>/editar", methods=["GET", "POST"])
def editar_turma(turma_id: int):
    """Edita os dados de uma turma."""
    servico = CursoService()
    turma = servico.obter_turma(turma_id)
    if turma is None:
        flash("Turma não encontrada.", "error")
        return redirect(url_for("admin.cursos"))

    formulario = TurmaForm(obj=turma)

    if formulario.validate_on_submit():
        try:
            servico.atualizar_turma(
                turma,
                _dados_do_formulario(formulario),
            )
        except ValueError as erro:
            flash(str(erro), "error")
        else:
            flash("Turma atualizada com sucesso.", "success")
            return redirect(
                url_for("admin.turmas_do_curso", curso_id=turma.curso_id)
            )

    return render_template(
        "admin/cursos/turma_formulario.html",
        formulario=formulario,
        curso=turma.curso,
        turma=turma,
        titulo_pagina=f"Editar turma: {turma.nome}",
    )


@bp.post("/turmas/<int:turma_id>/ativar")
def ativar_turma(turma_id: int):
    """Ativa uma turma."""
    servico = CursoService()
    turma = servico.obter_turma(turma_id)
    if turma is None:
        flash("Turma não encontrada.", "error")
        return redirect(url_for("admin.cursos"))

    servico.definir_situacao_turma(turma, True)
    flash("Turma ativada com sucesso.", "success")
    return redirect(
        _destino_admin("admin.turmas_do_curso", curso_id=turma.curso_id)
    )


@bp.post("/turmas/<int:turma_id>/desativar")
def desativar_turma(turma_id: int):
    """Desativa uma turma sem apagar seu histórico."""
    servico = CursoService()
    turma = servico.obter_turma(turma_id)
    if turma is None:
        flash("Turma não encontrada.", "error")
        return redirect(url_for("admin.cursos"))

    servico.definir_situacao_turma(turma, False)
    flash("Turma desativada com sucesso.", "success")
    return redirect(
        _destino_admin("admin.turmas_do_curso", curso_id=turma.curso_id)
    )


@bp.post("/turmas/<int:turma_id>/excluir")
def excluir_turma(turma_id: int):
    """Exclui uma turma somente quando não há inscrições vinculadas."""
    servico = CursoService()
    turma = servico.obter_turma(turma_id)
    if turma is None:
        flash("Turma não encontrada.", "error")
        return redirect(url_for("admin.cursos"))

    curso_id = turma.curso_id
    try:
        servico.excluir_turma(turma)
    except ValueError as erro:
        flash(str(erro), "error")
    else:
        flash("Turma excluída com sucesso.", "success")

    return redirect(
        url_for("admin.turmas_do_curso", curso_id=curso_id)
    )


def _dados_do_formulario(formulario) -> dict[str, object]:
    campos = CAMPOS_CURSO if isinstance(formulario, CursoForm) else CAMPOS_TURMA
    return {campo: getattr(formulario, campo).data for campo in campos}


def _destino_admin(endpoint: str, **valores) -> str:
    """Volta para a listagem anterior quando o formulário veio dela."""
    proximo = request.form.get("proximo") or request.args.get("proximo")
    if proximo and proximo.startswith("/admin/"):
        return proximo
    return url_for(endpoint, **valores)
