# Documentação de estudo — Módulo de Cursos

Este documento explica o módulo **Gerenciamento e Apresentação de Cursos**
(Pessoa A). O objetivo é servir de guia para estudar o código e apresentar o
projeto, sem substituir a leitura dos arquivos.

## 1. Visão geral

O catálogo é focado em **cursos gratuitos do SENAC em Sobral**. Não há cursos
pagos no sistema: o painel não permite cadastrá-los, as rotas de compra foram
removidas e a migração `f6a7b8c9d0e1` exclui cursos pagos eventualmente
existentes.

O módulo é responsável por:

- catálogo público de cursos gratuitos e ativos de Sobral;
- página inicial com cursos em destaque;
- detalhe público do curso;
- cadastro, edição, ativação, desativação e exclusão de cursos;
- cadastro, edição, ativação, desativação e exclusão de turmas;
- horários, períodos e controle de vagas por turma;
- link externo único para `https://cursos.ce.senac.br/` na navbar e na home;
- integração de dados com o módulo de inscrições.

A cidade padrão fica em `CIDADE_PADRAO` (`Sobral`) e o link externo em
`PORTAL_CURSOS_URL`, ambos em `app/config.py` e configuráveis por variáveis de
ambiente.

## 2. Principais arquivos e responsabilidades

| Arquivo | Responsabilidade |
| --- | --- |
| `app/models/curso.py` | Modelo `Curso`, cidade, relacionamentos, restrições e cálculos de vagas. |
| `app/models/turma.py` | Modelo `Turma`, horários, período, situação e cálculos de vagas da turma. |
| `app/services/curso_service.py` | Regras de negócio, filtro por cidade, validações, slug e persistência. |
| `app/forms/curso.py` | Formulários `CursoForm` e `TurmaForm` (WTForms/Flask-WTF). |
| `app/blueprints/catalogo/routes.py` | Rotas públicas: listagem e detalhe. |
| `app/blueprints/main/routes.py` | Página inicial com o link para o portal do Ceará. |
| `app/blueprints/admin/routes.py` | Rotas administrativas de cursos e turmas. |
| `app/templates/catalogo/lista_cursos.html` | Catálogo com busca por nome/descrição. |
| `app/templates/catalogo/detalhe_curso.html` | Detalhe, turmas, vagas e pré-inscrição. |
| `app/templates/components/curso_card.html` | Card reutilizável de curso. |
| `app/templates/components/navbar.html` | Link externo único para o portal de cursos do Ceará; sem link de login público. |
| `app/templates/admin/cursos/lista.html` | Listagem administrativa de cursos. |
| `app/templates/admin/cursos/formulario.html` | Formulário de curso com campo `cidade`. |
| `app/static/css/style.css` | Identidade visual e responsividade. |
| `tests/test_cursos.py` | Testes do módulo de cursos, turmas, vagas e rotas. |
| `migrations/versions/f6a7b8c9d0e1_cidade_sobral_e_remove_cursos_pagos.py` | Adiciona `cidade`, exclui cursos pagos. |
| `migrations/versions/a2b3c4d5e6f7_cpf_unico_global.py` | Torna o CPF único globalmente nas inscrições. |

## 3. Fluxo de uma requisição

### 3.1 Detalhe público de um curso

1. O navegador acessa `GET /cursos/<curso_id>`.
2. `detalhe` em `app/blueprints/catalogo/routes.py` recebe o pedido.
3. A função chama `CursoService.obter_curso(curso_id)`.
4. `curso_esta_visivel` exige curso ativo, gratuito e da cidade configurada.
5. Se não estiver visível, a rota responde `404`.
6. `listar_turmas(curso_id, apenas_ativas=True)` carrega as turmas ativas.
7. O template `catalogo/detalhe_curso.html` recebe `curso` e `turmas`.
8. O template usa `aceita_pre_inscricao`, `possui_vagas`, `turma.disponivel`,
   `turma.horario_formatado` e `turma.vagas_disponiveis`.

### 3.2 Cadastro administrativo de curso

1. O administrador acessa `GET /admin/cursos/novo`.
2. O `before_request` `exigir_autenticacao` exige login.
3. `novo_curso` cria um `CursoForm` com `cidade` preenchida com `Sobral`.
4. No `POST`, `validate_on_submit()` executa as validações.
5. `_dados_do_formulario` extrai os campos definidos em `CAMPOS_CURSO`.
6. `CursoService.criar_curso(dados)` força `tipo = GRATUITO`, limpa
   `link_externo`/`valor` e persiste o curso.
7. A rota redireciona para o gerenciamento de turmas do curso criado.

## 4. Modelo `Curso`

Arquivo: `app/models/curso.py` — classe `Curso`.

### 4.1 Campos principais

| Campo | Uso |
| --- | --- |
| `id` | Identificador interno. |
| `titulo` | Nome exibido no catálogo. |
| `slug` | Identificador amigável e único para URL. |
| `cidade` | Cidade da oferta; padrão `Sobral`, obrigatória e indexada. |
| `descricao` | Texto de divulgação. |
| `tipo` | Mantido no banco por compatibilidade; sempre `GRATUITO`. |
| `carga_horaria` | Carga horária em horas. |
| `data_inicio` / `data_fim` | Período geral do curso. |
| `vagas` | Vagas de referência quando não há turmas com vagas próprias. |
| `imagem_url` | Imagem do card. |
| `ativo` | Publicação do curso no catálogo. |
| `turmas` | Relacionamento com `Turma`. |
| `inscricoes` | Relacionamento com `Inscricao`. |

As restrições em `__table_args__` garantem no banco:

- cidade presente;
- tipo válido;
- vagas e carga horária não negativas;
- data final maior ou igual à inicial.

As colunas legadas `link_externo` e `valor` permanecem no esquema apenas para
compatibilidade com o histórico, mas não são usadas pelo fluxo atual.

### 4.2 Propriedades importantes

| Propriedade | Comportamento |
| --- | --- |
| `situacao` | Retorna `"ativo"` ou `"inativo"`. |
| `aceita_pre_inscricao` | Curso não inativo; indica elegibilidade para pré-inscrição. |
| `turmas_ativas` | Lista somente turmas não inativas. |
| `vagas_ocupadas` | Inscrições do curso cujo status não é `CANCELADA`. |
| `vagas_disponiveis` | Soma das vagas restantes das turmas ativas ou, sem turmas, `vagas - vagas_ocupadas`. Retorna `None` quando não há limite. |
| `possui_vagas` | Curso não inativo com pelo menos uma turma disponível ou, sem turmas, com limite de referência que permita inscrição. |

## 5. Modelo `Turma`

Arquivo: `app/models/turma.py` — classe `Turma`.

### 5.1 Campos principais

| Campo | Uso |
| --- | --- |
| `id` | Identificador da turma. |
| `curso_id` | Curso ao qual a turma pertence. |
| `nome` | Nome ou código da turma (ex.: “Turma Manhã”). |
| `dias_semana` | Dias de aula em texto. |
| `hora_inicio` / `hora_fim` | Horário da turma. |
| `data_inicio` / `data_fim` | Período da turma. |
| `vagas` | Limite de vagas; `None` significa sem limite. |
| `ativo` | Situação da turma. |
| `inscricoes` | Inscrições vinculadas à turma. |

As restrições em `__table_args__` garantem vagas não negativas, horário final
maior que o inicial e data final maior ou igual à inicial.

### 5.2 Propriedades importantes

| Propriedade | Comportamento |
| --- | --- |
| `situacao` | Retorna `"ativa"` ou `"inativa"`. |
| `vagas_ocupadas` | Inscrições da turma cujo status não é `CANCELADA`. |
| `vagas_disponiveis` | `vagas - vagas_ocupadas`, nunca menor que zero; `None` se ilimitada. |
| `tem_vagas` | `True` se não há limite ou se ainda existe vaga. |
| `disponivel` | Turma ativa, de curso ativo e com vaga disponível. |
| `horario_formatado` | Retorna algo como `"18:00 às 20:00"` ou `"Horário a definir"`. |

## 6. `CursoService`

Arquivo: `app/services/curso_service.py` — classe `CursoService`.

### 6.1 Consultas

| Método | Responsabilidade |
| --- | --- |
| `listar_cursos_publicos(termo, cidade)` | Lista cursos ativos, gratuitos e da cidade configurada, com busca por título/descrição. |
| `listar_todos(termo, situacao)` | Lista cursos no painel, incluindo inativos, com filtros. |
| `obter_curso(curso_id)` | Busca um curso pelo ID. |
| `listar_turmas(curso_id, apenas_ativas)` | Lista turmas ordenadas por nome. |
| `listar_turmas_disponiveis(curso_id)` | Lista turmas ativas que ainda têm vagas. |
| `obter_turma(turma_id)` | Busca uma turma pelo ID. |

A função `cidade_padrao()` lê `current_app.config["CIDADE_PADRAO"]` e é usada
tanto na listagem pública quanto em `curso_esta_visivel`.

### 6.2 Escrita

| Método | Responsabilidade |
| --- | --- |
| `criar_curso(dados)` | Cria e persiste um curso. |
| `atualizar_curso(curso, dados)` | Atualiza um curso existente. |
| `definir_situacao(curso, ativo)` | Ativa ou desativa um curso. |
| `excluir_curso(curso)` | Exclui curso sem inscrições; bloqueia quando há histórico. |
| `criar_turma(curso_id, dados)` | Cria uma turma vinculada ao curso. |
| `atualizar_turma(turma, dados)` | Atualiza uma turma existente. |
| `definir_situacao_turma(turma, ativo)` | Ativa ou desativa uma turma. |
| `excluir_turma(turma)` | Exclui turma sem inscrições; bloqueia quando há histórico. |

### 6.3 Validações do curso

A função `_aplicar_dados_do_curso` valida:

- título obrigatório;
- descrição obrigatória;
- cidade obrigatória, com no máximo 100 caracteres;
- carga horária maior que zero quando informada;
- vagas não negativas;
- data final não anterior à inicial;
- geração de slug único.

O serviço sempre grava `tipo = TipoCurso.GRATUITO`, `link_externo = None` e
`valor = None`, mesmo que o chamador envie valores diferentes.

### 6.4 Validações da turma

A função `_aplicar_dados_da_turma` valida:

- nome obrigatório;
- horário de início e fim informados em conjunto;
- horário final posterior ao inicial;
- data final não anterior à inicial;
- vagas não negativas.

### 6.5 Slug único

`gerar_slug` remove acentos, troca caracteres especiais por hífen e converte
para minúsculas. `CursoService._slug_unico` verifica o banco e acrescenta
sufixos numéricos quando necessário:

- `excel-basico`
- `excel-basico-2`
- `excel-basico-3`

Na edição, o próprio curso é ignorado na verificação para evitar conflito com o
slug atual.

## 7. Rotas

### 7.1 Rotas públicas

Arquivo: `app/blueprints/catalogo/routes.py`.

| Rota | Função | Comportamento |
| --- | --- | --- |
| `GET /cursos/` | `listar` | Lista cursos ativos, gratuitos e de Sobral, com busca `q`. |
| `GET /cursos/<id>` | `detalhe` | Exibe curso visível, turmas ativas e vagas; retorna 404 caso contrário. |

A antiga rota `catalogo.comprar` foi removida: qualquer requisição para
`/cursos/<id>/comprar` retorna `404`.

### 7.2 Rotas administrativas

Arquivo: `app/blueprints/admin/routes.py`. Todas são protegidas pelo
`before_request` `exigir_autenticacao`.

| Rota | Função |
| --- | --- |
| `GET /admin/` | `dashboard` |
| `GET /admin/cursos` | `cursos` |
| `GET/POST /admin/cursos/novo` | `novo_curso` |
| `GET/POST /admin/cursos/<id>/editar` | `editar_curso` |
| `POST /admin/cursos/<id>/ativar` | `ativar_curso` |
| `POST /admin/cursos/<id>/desativar` | `desativar_curso` |
| `POST /admin/cursos/<id>/excluir` | `excluir_curso` |
| `GET /admin/cursos/<id>/turmas` | `turmas_do_curso` |
| `GET/POST /admin/cursos/<id>/turmas/nova` | `nova_turma` |
| `GET/POST /admin/turmas/<id>/editar` | `editar_turma` |
| `POST /admin/turmas/<id>/ativar` | `ativar_turma` |
| `POST /admin/turmas/<id>/desativar` | `desativar_turma` |
| `POST /admin/turmas/<id>/excluir` | `excluir_turma` |

As rotas não concentram regras de negócio: recebem a requisição, chamam o
serviço, tratam `ValueError` com `flash` e redirecionam.

## 8. Formulários

Arquivo: `app/forms/curso.py`.

### 8.1 `CursoForm`

Valida:

- título obrigatório e com no máximo 150 caracteres;
- descrição obrigatória;
- cidade obrigatória e com no máximo 100 caracteres;
- carga horária mínima 1;
- vagas não negativas;
- data final não anterior à inicial (`validate_data_fim`);
- URL de imagem em formato válido.

Os campos de tipo, valor e link externo foram removidos. Não há mais JavaScript
condicional para cursos pagos: `main.js` apenas fecha mensagens flash.

### 8.2 `TurmaForm`

Valida:

- nome obrigatório e com no máximo 100 caracteres;
- horário de início e fim em conjunto (`validate_hora_inicio`);
- horário final posterior ao inicial (`validate_hora_fim`);
- data final não anterior à inicial (`validate_data_fim`);
- vagas não negativas.

## 9. Templates

### 9.1 Card de curso

Arquivo: `app/templates/components/curso_card.html` — macro `curso_card`.

Mostra:

- imagem ou letra inicial;
- badge `Gratuito · <cidade>`;
- título com link para o detalhe;
- descrição resumida;
- carga horária;
- disponibilidade de vagas;
- botão “Ver detalhes”;
- botão “Pré-inscrição” somente quando elegível **e** com vagas.

### 9.2 Catálogo

Arquivo: `app/templates/catalogo/lista_cursos.html`.

Variáveis recebidas da rota:

- `cursos`: lista de cursos visíveis;
- `termo`: busca digitada.

### 9.3 Detalhe do curso

Arquivo: `app/templates/catalogo/detalhe_curso.html`.

Variáveis:

- `curso`: objeto `Curso`;
- `turmas`: turmas ativas do curso.

Decisões feitas no template:

- pré-inscrição aparece somente se `aceita_pre_inscricao` e `possui_vagas`;
- turmas ativas são listadas com dias, horário, período e vagas;
- turma sem vagas recebe o selo “Vagas esgotadas”;
- curso sem turmas permite pré-inscrição quando ainda há disponibilidade.

### 9.4 Painel administrativo

- `admin/cursos/lista.html`: coluna `Cidade` e ações de editar, gerenciar turmas,
  ativar, desativar e excluir.
- `admin/cursos/formulario.html`: cadastro e edição somente de cursos
  gratuitos, com campo `cidade`.
- `admin/cursos/turmas.html`: lista de turmas, situação, ocupação e ações.
- `admin/cursos/turma_formulario.html`: cadastro e edição de turma.
- `admin/dashboard.html`: indicadores e cursos recentes.

### 9.5 Link externo único

O link para `https://cursos.ce.senac.br/` aparece em:

- `app/templates/components/navbar.html` — “Outros cursos no SENAC”;
- `app/templates/main/index.html` — “Acesse o portal de cursos do SENAC Ceará”.

Ambos usam `target="_blank"` e `rel="noopener noreferrer"`.

## 10. Controle de vagas

### 10.1 Turma

```
vagas_ocupadas = inscrições da turma com status != CANCELADA
vagas_disponiveis = max(vagas - vagas_ocupadas, 0)
tem_vagas = vagas is None OR vagas_disponiveis > 0
disponivel = turma.ativo AND curso.ativo AND tem_vagas
```

- `vagas = None`: turma ilimitada.
- `vagas = 0`: turma sem vagas.
- Inscrição cancelada deixa de ocupar vaga.
- Turma inativa não é considerada disponível.

### 10.2 Curso

```
turmas_ativas = turmas com ativo != False

se existem turmas_ativas:
    se alguma turma é ilimitada:
        vagas_disponiveis = None
    senão:
        vagas_disponiveis = soma(vagas_disponiveis das turmas ativas)
senão:
    se curso.vagas é None:
        vagas_disponiveis = None
    senão:
        vagas_disponiveis = max(curso.vagas - curso.vagas_ocupadas, 0)
```

`possui_vagas` é `True` quando o curso não está inativo e existe pelo menos uma
turma ativa disponível. Sem turmas, usa o limite de referência do curso.

### 10.3 Exibição pública

- Catálogo e detalhe não exibem cursos inativos, pagos ou de outra cidade.
- A página de detalhe não exibe turmas inativas.
- Cards só oferecem pré-inscrição quando o curso é elegível e possui vaga.
- Turmas lotadas aparecem como indisponíveis.

## 11. Integração com o módulo de inscrições

### 11.1 Dados disponíveis

| Necessidade | Como obter |
| --- | --- |
| Identificador do curso | `curso.id` |
| Nome do curso | `curso.titulo` |
| Cidade do curso | `curso.cidade` |
| Situação do curso | `curso.ativo` / `curso.situacao` |
| Curso aceita pré-inscrição | `curso.aceita_pre_inscricao` |
| Identificador da turma | `turma.id` |
| Nome da turma | `turma.nome` |
| Curso da turma | `turma.curso` / `turma.curso_id` |
| Horário | `turma.hora_inicio`, `turma.hora_fim`, `turma.horario_formatado` |
| Dias e período | `turma.dias_semana`, `turma.data_inicio`, `turma.data_fim` |
| Situação da turma | `turma.ativo` / `turma.situacao` |
| Disponibilidade | `turma.vagas_disponiveis`, `turma.tem_vagas`, `turma.disponivel` |

O contrato em `app/contracts.py` continua sendo o ponto de referência entre os
módulos.

### 11.2 Regras aplicadas

`InscricaoService.criar_pre_inscricao` valida curso ativo/elegível, turma
pertencente ao curso, turma ativa, disponibilidade e CPF antes de persistir com
`status = StatusInscricao.RECEBIDA`. O CPF é obrigatório, validado e normalizado
para `000.000.000-00`; uma pessoa só pode se inscrever uma vez no sistema,
independentemente do curso.

### 11.3 Proteção pública

- Catálogo e detalhe escondem cursos inativos ou de outra cidade.
- Detalhe esconde turmas inativas.
- Links de pré-inscrição só aparecem quando há vaga.
- A rota de pré-inscrição vincula `Inscricao.turma` quando `turma_id` é enviado
  pelo detalhe do curso.

Em bancos com alta concorrência, use `SELECT ... FOR UPDATE` ou travamento
otimista para evitar que duas requisições ocupem a última vaga.

## 12. Testes

Arquivo principal: `tests/test_cursos.py`.

Os testes cobrem:

- criação de curso gratuito, slug único e cidade padrão;
- criação em outra cidade e ativação/desativação;
- atualização preservando slug;
- validação de descrição, cidade, datas e horários;
- múltiplas turmas e controle de vagas por turma;
- cancelamento liberando vaga;
- exclusão bloqueada quando há inscrições;
- catálogo somente com cursos de Sobral;
- detalhe de curso de outra cidade retornando 404;
- rota de compra removida;
- link externo único na navbar e na home;
- cadastro, edição e ações administrativas;
- proteção das rotas administrativas.

Comando:

```bash
source .venv/bin/activate
python -m pytest -q
```

Resultado da última execução:

```text
88 passed
```

## 13. Como executar o projeto

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
flask --app run.py db upgrade
flask --app run.py seed-demo
flask --app run.py run --debug
```

Acesse:

- página inicial: <http://127.0.0.1:5000/>
- catálogo: <http://127.0.0.1:5000/cursos>
- painel: <http://127.0.0.1:5000/admin/>

## 14. Roteiro rápido de estudo

1. Leia `app/models/curso.py` e `app/models/turma.py`.
2. Entenda as propriedades de vagas: `vagas_ocupadas`, `vagas_disponiveis`,
   `tem_vagas`, `disponivel` e `possui_vagas`.
3. Leia `app/services/curso_service.py`, começando por `criar_curso`,
   `listar_cursos_publicos`, `atualizar_curso` e `_slug_unico`.
4. Leia `app/forms/curso.py` para entender a validação de entrada.
5. Siga uma requisição pública em `app/blueprints/catalogo/routes.py`.
6. Siga uma requisição administrativa em `app/blueprints/admin/routes.py`.
7. Compare as variáveis passadas pelas rotas com o uso nos templates.
8. Leia `tests/test_cursos.py` para ver as regras em execução.

## 15. Pendências e limites do módulo

- O bloqueio de vagas usa a transação do SQLAlchemy; em SQLite, com escritas
  concorrentes, ainda pode ser necessário travamento explícito.
- A edição do título de um curso recalcula o slug; links antigos podem mudar.
- Não há paginação nas listagens administrativas.
- As colunas `link_externo` e `valor` permanecem apenas para compatibilidade
  histórica e devem ser removidas em uma futura limpeza de esquema.
- O módulo não usa dados reais de alunos; todos os exemplos e testes usam dados
  fictícios.
