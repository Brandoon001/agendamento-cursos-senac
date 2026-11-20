"""Testes de regressão da interface administrativa."""

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


def test_dashboard_reserva_altura_fixa_para_o_grafico(client_autenticado):
    resposta = client_autenticado.get("/admin/")

    assert resposta.status_code == 200
    html = resposta.get_data(as_text=True)
    assert 'class="chart-box"' in html
    assert 'id="grafico-inscricoes"' in html
    assert 'height="240"' not in html
