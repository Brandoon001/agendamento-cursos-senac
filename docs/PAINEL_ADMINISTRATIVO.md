# Painel administrativo

## Objetivo

Documentar o uso operacional do painel em `/admin`, suas telas, filtros e rotinas. Veja também [Rotas](ROTAS.md), [Fluxos de negócio](FLUXOS_DE_NEGOCIO.md) e [Interface](INTERFACE.md).

## Acesso

- URL: `/auth/login`.
- Somente o administrador criado por `flask --app run.py criar-admin` pode entrar.
- Todas as rotas `/admin/*` exigem sessão autenticada.
- O link de login não aparece na navegação pública; o endereço é acessado diretamente.
- `next` recebido no login é aceito somente se for caminho interno.

## Estrutura do painel

`app/templates/components/admin_shell.html` fornece:

- topbar com marca, link “Ver site” e formulário de logout;
- sidebar com `Painel`, `Cursos e turmas`, `Inscrições` e ação rápida `Novo curso`;
- marcação `active` e `aria-current="page"` conforme `request.endpoint`.

`app/templates/admin_base.html` define os blocos `title`, `content`, `head` e `scripts`.

## Dashboard

Rota: `admin.dashboard`. Template: `app/templates/admin/dashboard.html`.

Dados enviados pela view:

| Variável | Origem |
| --- | --- |
| `total_cursos` | `len(CursoService().listar_todos())` |
| `cursos_ativos` | cursos com `ativo=True` |
| `total_turmas` | `COUNT(*)` de `turmas` |
| `total_inscricoes` | `COUNT(*)` de `inscricoes` |
| `contadores_inscricoes` | `InscricaoService.contar_por_status()` |
| `status_labels` | `STATUS_LABELS` |
| `cursos_recentes` | 5 cursos mais recentes por `criado_em` |

Blocos visuais:

1. quatro `stat_card` principais;
2. cards por situação de inscrição, incluindo situações com zero;
3. tabela de cursos recentes;
4. gráfico doughnut Chart.js 4.6.1.

O gráfico usa `maintainAspectRatio: false` dentro de `.chart-box` (`height: 16rem` em `app/static/css/style.css:763-766`). Isso evita crescimento indefinido do canvas.

## Inscrições

Rota: `admin.inscricoes`. Template: `app/templates/admin/inscricoes.html`.

### Filtros

| Campo | Parâmetro | Opções |
| --- | --- | --- |
| Busca | `q` | nome, CPF ou e-mail |
| Situação | `status` | todas + cinco valores de `StatusInscricao` |
| Curso | `curso_id` | todos + cursos retornados por `listar_todos()` |

O link “Limpar” aparece quando pelo menos um filtro está ativo.

### Indicadores por situação

Os cards são gerados a partir de `status_opcoes = StatusInscricao` e `contadores.get(opcao, 0)`. Cada card links para `/admin/inscricoes?status=<valor>`.

### Tabela

Colunas: protocolo, candidato/CPF, contato, curso/turma, situação, data de registro e atualização de situação.

O `<select>` de situação faz POST para `admin.alterar_status_inscricao`; o servidor registra `administrador_id` e preserva os filtros.

### Exportação

`GET /admin/inscricoes/exportar` reusa os mesmos filtros e baixa `inscricoes-YYYY-MM-DD.xlsx`. O XLSX contém 11 colunas, incluindo protocolo, contato, turma, situação e observações.

## Cursos

Rota: `admin.cursos`. Template: `app/templates/admin/cursos/lista.html`.

- filtros `q` e `situacao`;
- ações de editar, gerenciar turmas, ativar/desativar e excluir;
- ativação/desativação usam POST com CSRF;
- exclusão só é permitida quando não há inscrições; caso contrário, flash orienta arquivar.

### Formulário de curso

Templates: `app/templates/admin/cursos/formulario.html`.

Campos principais: nome, slug opcional, descrição, cidade, carga horária, datas, vagas de referência, URL da imagem, upload e ativo.

Ao salvar:

1. upload é validado e salvo, se houver;
2. `CursoService` normaliza dados e gera slug único;
3. em erro, nova imagem é removida;
4. em sucesso com imagem substituída, imagem antiga é removida;
5. após a criação, usuário vai para a tela de turmas.

## Turmas

Rotas em `app/blueprints/admin/routes.py:244-376`.

Templates:

- `app/templates/admin/cursos/turmas.html`;
- `app/templates/admin/cursos/turma_formulario.html`.

Campos: nome/código, dias da semana, início/fim, datas, vagas e ativo.

Regras operacionais:

- turma com inscrição deve ser desativada, não excluída;
- horário de término deve ser posterior ao de início;
- início e fim devem ser informados juntos;
- `vagas` vazio significa ilimitado;
- disponibilidade pública também depende do curso estar ativo.

## Convenções de interface no admin

- Breadcrumbs via macro `breadcrumb()`.
- Títulos usam `.admin-page-header`.
- Ações usam `.admin-actions`.
- Tabelas usam `.table.senac-table` dentro de `.table-panel`.
- Confirmações destrutivas usam `data-confirm` e SweetAlert2.
- Flash messages aparecem no topo e são removidas automaticamente após 7 s quando `success`.

## Rotinas operacionais

### Publicar novo curso

1. Criar curso.
2. Cadastrar ao menos uma turma.
3. Conferir cidade e datas.
4. Ativar curso e turma.
5. Validar no catálogo público.

### Arquivar curso encerrado

1. Desativar turmas do curso.
2. Desativar curso.
3. Não excluir se houver inscrições.

### Atualizar situações em lote

Não há ação em lote. Atualize cada linha na tabela de inscrições e use os filtros para localizar grupos.

### Conferir exportação

Filtre na tela, abra o link “Exportar para Excel” e confirme que a contagem de linhas corresponde ao texto “N inscrição(ões) encontrada(s)”.

## Troubleshooting

| Sintoma | Causa provável | Ação |
| --- | --- | --- |
| Muitas linhas em branco nos cards de situação | whitespace de Jinja | usar `{%- ... -%}` nos loops, como em `admin/inscricoes.html` |
| Gráfico crescendo sem limite | canvas sem container dimensionado | manter `.chart-box` |
| Status ausente no dashboard | contador sem chave zero | usar `contar_por_status()` |
| Exclusão recusada | curso/turma com inscrições | desativar em vez de excluir |
| POST sem efeito | CSRF ausente | incluir `csrf_token()` no formulário |

## Leitura complementar

- [Rotas](ROTAS.md)
- [Serviços](SERVICOS.md)
- [Interface](INTERFACE.md)
