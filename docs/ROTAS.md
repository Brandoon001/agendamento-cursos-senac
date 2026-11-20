# Rotas

## Objetivo

Tabela completa de endpoints HTTP do Agenda-Senac, parâmetros, permissões e destinos. Veja também [Arquitetura](ARQUITETURA.md), [Fluxos de negócio](FLUXOS_DE_NEGOCIO.md) e [Painel administrativo](PAINEL_ADMINISTRATIVO.md).

## Convenções

- Rotas são registradas em cinco blueprints: `main`, `catalogo`, `inscricoes`, `auth` e `admin`.
- Registro central: `app/blueprints/__init__.py`.
- `POST` que altera estado exige token CSRF.
- Rotas administrativas são protegidas por `@bp.before_request @login_required` em `app/blueprints/admin/routes.py:34-38`.
- Usuários não autenticados são redirecionados para `auth.login?next=...`.
- Respostas de erro usam os templates de `app/templates/errors/`.

## Rotas públicas

| Método | URL | Endpoint | Descrição | Resposta |
| --- | --- | --- | --- | --- |
| GET | `/` | `main.index` | Página inicial com até 6 cursos | `main/index.html` |
| GET | `/cursos` | `catalogo.listar` | Catálogo com busca `q` opcional | `catalogo/lista_cursos.html` |
| GET | `/cursos/<curso_id>` | `catalogo.detalhe` | Detalhe do curso visível | `catalogo/detalhe_curso.html` ou `404` |
| GET/POST | `/inscricoes/<curso_id>/pre-inscricao` | `inscricoes.pre_inscricao` | Formulário de pré-inscrição | `inscricoes/pre_inscricao.html` ou redirect |
| GET | `/inscricoes/<inscricao_id>/confirmacao` | `inscricoes.confirmacao` | Comprovante privado | `inscricoes/confirmacao.html` ou `404` |
| GET/POST | `/auth/login` | `auth.login` | Login administrativo | `auth/login.html` ou redirect |
| POST | `/auth/logout` | `auth.logout` | Encerra sessão | redirect para `main.index` |

`/cursos` usa `strict_slashes=False`, então `/cursos/` também funciona.

`catalogo.detalhe` e `inscricoes.pre_inscricao` usam `curso_esta_visivel()`; curso inativo, pago ou de outra cidade retorna `404`.

### Parâmetros de consulta

| Rota | Parâmetro | Uso |
| --- | --- | --- |
| `catalogo.listar` | `q` | busca por título/descrição |
| `inscricoes.pre_inscricao` | `turma_id` | pré-seleciona a turma; também aceito no body do POST |
| `auth.login` | `next` | destino interno após login; validado por `_destino_seguro()` |

## Rotas administrativas

Todas exigem login.

| Método | URL | Endpoint | Descrição |
| --- | --- | --- | --- |
| GET | `/admin/` | `admin.dashboard` | Indicadores, cards, gráfico e cursos recentes |
| GET | `/admin/inscricoes` | `admin.inscricoes` | Lista filtrável de inscrições |
| POST | `/admin/inscricoes/<inscricao_id>/status` | `admin.alterar_status_inscricao` | Atualiza situação e responsável |
| GET | `/admin/inscricoes/exportar` | `admin.exportar_inscricoes` | Download XLSX com os filtros atuais |
| GET | `/admin/cursos` | `admin.cursos` | Lista cursos, ativos e inativos |
| GET/POST | `/admin/cursos/novo` | `admin.novo_curso` | Cadastro de curso |
| GET/POST | `/admin/cursos/<curso_id>/editar` | `admin.editar_curso` | Edição de curso |
| POST | `/admin/cursos/<curso_id>/ativar` | `admin.ativar_curso` | Ativa curso |
| POST | `/admin/cursos/<curso_id>/desativar` | `admin.desativar_curso` | Arquiva curso |
| POST | `/admin/cursos/<curso_id>/excluir` | `admin.excluir_curso` | Exclui curso sem inscrições |
| GET | `/admin/cursos/<curso_id>/turmas` | `admin.turmas_do_curso` | Gerencia turmas do curso |
| GET/POST | `/admin/cursos/<curso_id>/turmas/nova` | `admin.nova_turma` | Cadastro de turma |
| GET/POST | `/admin/turmas/<turma_id>/editar` | `admin.editar_turma` | Edição de turma |
| POST | `/admin/turmas/<turma_id>/ativar` | `admin.ativar_turma` | Ativa turma |
| POST | `/admin/turmas/<turma_id>/desativar` | `admin.desativar_turma` | Arquiva turma |
| POST | `/admin/turmas/<turma_id>/excluir` | `admin.excluir_turma` | Exclui turma sem inscrições |

### Filtros de inscrições

`admin.inscricoes` e `admin.exportar_inscricoes` leem:

| Parâmetro | Tipo | Efeito |
| --- | --- | --- |
| `q` | texto | busca em nome, CPF e e-mail |
| `status` | string | filtra por valor de `StatusInscricao`; inválido retorna lista vazia |
| `curso_id` | inteiro | filtra por curso |

`admin.alterar_status_inscricao` recebe os mesmos parâmetros na query string para preservar o filtro no retorno.

### Filtros de cursos

`admin.cursos` lê `q` (título/descrição) e `situacao` (`ativo` ou `inativo`).

### Redirects administrativos

`_destino_admin()` em `app/blueprints/admin/routes.py:437-449` aceita `proximo` somente quando:

- não tem esquema nem host;
- começa com `/admin/`;
- não começa com `//`.

Caso contrário, volta para o endpoint padrão informado.

## Rota estática

| Método | URL | Endpoint | Observação |
| --- | --- | --- | --- |
| GET | `/static/<path:filename>` | `static` | CSS, JS e uploads; fornecida pelo Flask |

## Erros

Registrados em `app/errors.py`:

| Erro | Template | Observação |
| --- | --- | --- |
| 400 | `errors/400.html` | Também usado para `CSRFError`, com `motivo` |
| 403 | `errors/403.html` | — |
| 404 | `errors/404.html` | — |
| 500 | `errors/500.html` | Faz rollback e loga a exceção |
| `CSRFError` | `errors/400.html` | Status HTTP 400 |

## Segurança por rota

| Grupo | Autenticação | CSRF |
| --- | --- | --- |
| Público (`main`, `catalogo`, `inscricoes`) | não | somente POST de pré-inscrição |
| `auth.login` | não; redireciona autenticado | sim |
| `auth.logout` | `login_required` | sim |
| `admin.*` | `before_request` com `login_required` | todos os POST |

## Como adicionar uma rota

1. Escolha o blueprint existente em `app/blueprints/`.
2. Decore a função em `routes.py` com `@bp.get`, `@bp.post` ou `@bp.route`.
3. Use `url_for("<blueprint>.<funcao>")` nos templates.
4. Chame serviços para regras de negócio.
5. Para POST, inclua token CSRF no formulário.
6. Atualize este documento e [Testes](TESTES.md).

Não é necessário alterar `app/blueprints/__init__.py` ao adicionar rotas dentro de um blueprint já registrado.

## Leitura complementar

- [Painel administrativo](PAINEL_ADMINISTRATIVO.md)
- [Segurança](SEGURANCA.md)
- [Interface](INTERFACE.md)
