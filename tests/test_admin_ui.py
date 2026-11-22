"""Testes de regressão da interface administrativa."""

from pathlib import Path

from app.services.curso_service import CursoService
from app.services.inscricao_service import InscricaoService


def test_painel_inscricoes_nao_repete_linhas_vazias_no_loop_de_situacao(
    client_autenticado,
):
    curso = CursoService().criar_curso(
        {
            "titulo": "Curso para contagem",
            "descricao": "Curso fictício usado em testes.",
            "cidade": "Sobral",
            "ativo": True,
        }
    )
    InscricaoService().criar_pre_inscricao(
        curso.id,
        {
            "nome_completo": "Aluno Fictício",
            "cpf": "529.982.247-25",
        },
    )

    resposta = client_autenticado.get("/admin/inscricoes?status=recebida")

    assert resposta.status_code == 200
    html = resposta.get_data(as_text=True)
    secao = html.split('aria-label="Inscrições por situação"', 1)[1].split(
        "</section>", 1
    )[0]
    assert secao.count('<a class="stat-card stat-card--link"') == 5
    assert "\n\n\n" not in secao


def test_sidebar_admin_mantem_atalhos_em_layout_vertical():
    css = (
        Path(__file__).resolve().parents[1] / "app/static/css/style.css"
    ).read_text(encoding="utf-8")

    assert ".navbar-nav.admin-sidebar {\n  flex-direction: column;\n}" in css


def test_sidebar_admin_fica_ao_lado_do_conteudo(client_autenticado):
    css = (
        Path(__file__).resolve().parents[1] / "app/static/css/style.css"
    ).read_text(encoding="utf-8")
    resposta = client_autenticado.get("/admin/")

    assert resposta.status_code == 200
    assert 'class="navbar-expand-md admin-sidebar-wrapper"' in resposta.get_data(
        as_text=True
    )
    assert '"sidebar content"' in css
    assert '"topbar topbar"' in css
    assert "position: sticky;\n    top: 0;\n    align-self: start;" in css
    assert "height: 100dvh;" in css


def test_acoes_rapidas_ficam_fora_do_menu_colapsavel(client_autenticado):
    html = client_autenticado.get("/admin/").get_data(as_text=True)
    menu = html.split('id="sidebar-menu"', 1)[1].split("</div>", 1)[0]

    assert "Ações rápidas" not in menu
    assert "Ações rápidas" in html
    assert "Gestão" not in html
    assert 'content="#004a8d"' in html


def test_paleta_usa_cores_oficiais_do_senac():
    css = (
        Path(__file__).resolve().parents[1] / "app/static/css/style.css"
    ).read_text(encoding="utf-8")

    assert "--senac-blue: #004a8d;" in css
    assert "--senac-accent: #f7941d;" in css
    assert "--senac-accent-light: #fdc180;" in css
    assert "--bs-primary-rgb: 0, 74, 141;" in css


def test_dashboard_reserva_altura_fixa_para_o_grafico(client_autenticado):
    resposta = client_autenticado.get("/admin/")

    assert resposta.status_code == 200
    html = resposta.get_data(as_text=True)
    assert 'class="chart-box"' in html
    assert 'id="grafico-inscricoes"' in html
    assert 'height="240"' not in html
