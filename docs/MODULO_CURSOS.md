# Documentação de estudo — Módulo de Cursos

Este documento explica o módulo **Gerenciamento e Apresentação de Cursos**
(Pessoa A). O objetivo é servir de guia para estudar o código e apresentar o
projeto, sem substituir a leitura dos arquivos.

## 1. Visão geral

O módulo é responsável por:

- catálogo público de cursos;
- página inicial com cursos em destaque;
- detalhe público do curso;
- cadastro, edição, ativação, desativação e exclusão de cursos;
- cadastro, edição, ativação, desativação e exclusão de turmas;
- horários, períodos e controle de vagas por turma;
- diferenciação entre curso gratuito e curso pago;
- integração de dados com o módulo de inscrições.

O módulo **não** implementa a persistência de inscrições nem o login. Essas
responsabilidades pertencem aos módulos de inscrições e autenticação. As rotas
administrativas usam o `login_required` já existente na fundação.

## 2. Principais arquivos e responsabilidades

| Arquivo | Responsabilidade |
| --- | --- |
| `app/models/curso.py` | Modelo `Curso`, relacionamentos, restrições e cálculos de vagas do curso. |
| `app/models/turma.py` | Modelo `Turma`, horários, período, situação e cálculos de vagas da turma. |
| `app/services/curso_service.py` | Regras de negócio de cursos e turmas, validações, slug e persistência. |
| `app/forms/curso.py` | Formulários `CursoForm` e `TurmaForm` (WTForms/Flask-WTF). |
| `app/blueprints/catalogo/routes.py` | Rotas públicas: listagem, detalhe e compra de curso pago. |
| `app/blueprints/main/routes.py` | Página inicial. |
| `app/blueprints/admin/routes.py` | Rotas administrativas de cursos e turmas. |
| `app/templates/catalogo/lista_cursos.html` | Página do catálogo com busca e filtro. |
| `app/templates/catalogo/detalhe_curso.html` | Página de detalhe, turmas, vagas e ações. |
| `app/templates/components/curso_card.html` | Card reutilizável de curso. |
| `app/templates/admin/cursos/lista.html` | Listagem administrativa de cursos. |
| `app/templates/admin/cursos/formulario.html` | Formulário de curso. |
| `app/templates/admin/cursos/turmas.html` | Gerenciamento de turmas de um curso. |
| `app/templates/admin/cursos/turma_formulario.html` | Formulário de turma. |
| `app/static/css/style.css` | Identidade visual e responsividade. |
| `app/static/js/main.js` | Exibição condicional dos campos de curso pago e fechamento de mensagens. |
| `tests/test_cursos.py` | Testes do módulo de cursos, turmas, vagas e rotas. |
| `migrations/versions/c3d4e5f6a7b8_modulo_de_cursos_e_turmas.py` | Criação da tabela `turmas` e vínculo `inscricoes.turma_id`. |

## 3. Fluxo de uma requisição

### 3.1 Detalhe público de um curso

1. O navegador acessa `GET /cursos/<curso_id>`.
2. A função `detalhe` em `app/blueprints/catalogo/routes.py` recebe o pedido.
3. Ela chama `CursoService.obter_curso(curso_id)`.
4. A função `curso_esta_visivel` verifica se o curso existe e está ativo.
5. Se o curso não estiver visível, a rota responde `404`.
6. `CursoService.listar_turmas(curso_id, apenas_ativas=True)` carrega apenas as
   turmas ativas.
7. O template `catalogo/detalhe_curso.html` recebe `curso` e `turmas`.
8. O template usa as propriedades do modelo para decidir o que mostrar:
   - `curso.e_pago` / `curso.e_gratuito`;
   - `curso.aceita_pre_inscricao`;
   - `curso.possui_vagas`;
   - `turma.disponivel`;
   - `turma.horario_formatado`;
   - `turma.vagas_disponiveis`.

### 3.2 Cadastro administrativo de curso

1. O administrador acessa `GET /admin/cursos/novo`.
2. O Blueprint `admin` já exige autenticação por meio do `before_request`
   `exigir_autenticacao` em `app/blueprints/admin/routes.py`.
3. A função `novo_curso` cria um `CursoForm`.
4. No `POST`, `formulario.validate_on_submit()` executa as validações do
   formulário.
5. Os dados são convertidos por `_dados_do_formulario`.
6. `CursoService.criar_curso(dados)` aplica as regras de negócio.
7. O serviço persiste e confirma a transação.
8. A rota redireciona para o gerenciamento de turmas do curso criado.

## 4. Modelo `Curso`

Arquivo: `app/models/curso.py` — classe `Curso`.

### 4.1 Campos principais

| Campo | Uso |
| --- | --- |
| `id` | Identificador interno. |
| `titulo` | Nome exibido no catálogo. |
| `slug` | Identificador amigável e único para URL. |
| `descricao` | Texto de divulgação. |
| `tipo` | `TipoCurso.PAGO` ou `TipoCurso.GRATUITO`. |
| `link_externo` | Obrigatório em curso pago; proibido em curso gratuito. |
| `valor` | Valor de referência de curso pago. |
| `carga_horaria` | Carga horária em horas. |
| `data_inicio` / `data_fim` | Período geral do curso. |
| `vagas` | Vagas de referência quando não há turmas com vagas próprias. |
| `imagem_url` | Imagem do card. |
| `ativo` | Publicação do curso no catálogo. |
| `turmas` | Relacionamento com `Turma`. |
| `inscricoes` | Relacionamento com `Inscricao`. |

As restrições em `__table_args__` garantem no banco:

- tipo válido;
- curso pago com link externo e curso gratuito sem link;
- valor e vagas não negativos;
- carga horária positiva;
- data final maior ou igual à inicial.

### 4.2 Propriedades importantes

| Propriedade | Comportamento |
| --- | --- |
| `situacao` | Retorna `"ativo"` ou `"inativo"`. |
| `e_pago` | `True` quando `tipo == TipoCurso.PAGO`. |
| `e_gratuito` | `True` quando `tipo == TipoCurso.GRATUITO`. |
| `aceita_pre_inscricao` | Curso gratuito e não inativo; indica elegibilidade para pré-inscrição. |
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
| `listar_cursos_publicos(termo, tipo)` | Lista apenas cursos ativos, com busca por título/descrição e filtro por tipo. |
| `listar_todos(termo, situacao)` | Lista cursos no painel, incluindo inativos, com filtros. |
| `obter_curso(curso_id)` | Busca um curso pelo ID. |
| `obter_link_compra(curso)` | Devolve o link de compra de um curso pago; lança `ValueError` se inválido. |
| `listar_turmas(curso_id, apenas_ativas)` | Lista turmas ordenadas por nome. |
| `listar_turmas_disponiveis(curso_id)` | Lista turmas ativas que ainda têm vagas. |
| `obter_turma(turma_id)` | Busca uma turma pelo ID. |

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

- tipo obrigatório e válido;
- título obrigatório;
- descrição obrigatória;
- curso pago precisa de link externo `http://` ou `https://`;
- curso gratuito não mantém link externo nem valor;
- carga horária maior que zero quando informada;
- vagas não negativas;
- valor não negativo;
- data final não anterior à inicial;
- geração de slug único.

### 6.4 Validações da turma

A função `_aplicar_dados_da_turma` valida:

- nome obrigatório;
- horário de início e fim informados em conjunto;
- horário final posterior ao inicial;
- data final não anterior à inicial;
- vagas não negativas.

### 6.5 Slug único

A função pública `gerar_slug` em `app/services/curso_service.py` remove acentos,
troca caracteres especiais por hífen e converte para minúsculas.

A função `CursoService._slug_unico` verifica o banco e acrescenta sufixos
numéricos quando necessário:

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
| `GET /cursos/` | `listar` | Lista cursos ativos, com busca `q` e filtro `tipo`. |
| `GET /cursos/<id>` | `detalhe` | Exibe curso ativo, turmas ativas e vagas; retorna 404 se inativo. |
| `GET /cursos/<id>/comprar` | `comprar` | Redireciona somente curso pago, ativo e com link externo. |

Arquivo: `app/blueprints/main/routes.py`.

| Rota | Função | Comportamento |
| --- | --- | --- |
| `GET /` | `index` | Exibe até seis cursos ativos na página inicial. |

### 7.2 Rotas administrativas

Arquivo: `app/blueprints/admin/routes.py`.

Todas são protegidas pelo `before_request` `exigir_autenticacao`, que usa
`login_required`.

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

As rotas não concentram regras de negócio: elas recebem a requisição, chamam o
serviço, tratam `ValueError` com `flash` e redirecionam.

## 8. Formulários

Arquivo: `app/forms/curso.py`.

### 8.1 `CursoForm`

Valida:

- título obrigatório e com no máximo 150 caracteres;
- descrição obrigatória;
- tipo obrigatório;
- link externo opcional, mas obrigatório para curso pago e proibido para
  gratuito (`validate_link_externo`);
- valor não negativo;
- carga horária mínima 1;
- vagas não negativas;
- data final não anterior à inicial (`validate_data_fim`);
- URLs de imagem e link externo em formato válido.

O template usa `data-tipo-curso` e `data-campo-pago`. O JavaScript em
`app/static/js/main.js` oculta e desabilita os campos de curso pago quando o tipo
selecionado é gratuito.

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

Recebe um `curso` e mostra:

- imagem ou letra inicial;
- badge de gratuito/pago;
- título com link para o detalhe;
- descrição resumida;
- carga horária;
- disponibilidade de vagas;
- botão “Ver detalhes”;
- botão “Comprar” para curso pago;
- botão “Pré-inscrição” somente para curso gratuito elegível **e** com vagas.

### 9.2 Catálogo

Arquivo: `app/templates/catalogo/lista_cursos.html`.

Variáveis recebidas da rota:

- `cursos`: lista de cursos ativos;
- `termo`: busca digitada;
- `tipo_selecionado`: tipo do filtro;
- `tipos`: enumeração `TipoCurso` para montar o `select`.

### 9.3 Detalhe do curso

Arquivo: `app/templates/catalogo/detalhe_curso.html`.

Variáveis:

- `curso`: objeto `Curso`;
- `turmas`: turmas ativas do curso.

Decisões feitas no template:

- curso pago mostra o botão de compra externa;
- curso gratuito mostra pré-inscrição somente se `aceita_pre_inscricao` e
  `possui_vagas`;
- turmas ativas são listadas com dias, horário, período e vagas;
- turma sem vagas recebe o selo “Vagas esgotadas”;
- curso pago com turmas também exibe os horários e o link de compra;
- curso gratuito sem turmas permite pré-inscrição quando ainda há
  disponibilidade.

### 9.4 Painel administrativo

- `admin/cursos/lista.html`: ações de editar, gerenciar turmas, ativar,
  desativar e excluir.
- `admin/cursos/formulario.html`: cadastro e edição de curso.
- `admin/cursos/turmas.html`: lista de turmas, situação, ocupação e ações.
- `admin/cursos/turma_formulario.html`: cadastro e edição de turma.
- `admin/dashboard.html`: indicadores e cursos recentes.

## 10. Controle de vagas

O controle é feito **por turma**, mas o curso também oferece uma visão agregada.

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

`possui_vagas` é `True` quando o curso não está inativo e existe pelo menos
uma turma ativa disponível. Sem turmas, usa o limite de referência do curso.
Curso inativo sempre retorna `False`.

### 10.3 Exibição pública

- O catálogo e o detalhe não exibem cursos inativos.
- A página de detalhe não exibe turmas inativas.
- Cards só oferecem pré-inscrição quando o curso é gratuito, elegível e possui
  vaga.
- Turmas lotadas aparecem como indisponíveis.
- O curso pago sempre direciona para o link externo individual.

## 11. Integração com o módulo de inscrições

### 11.1 Dados disponíveis

O módulo de inscrições consegue obter diretamente dos modelos:

| Necessidade | Como obter |
| --- | --- |
| Identificador do curso | `curso.id` |
| Nome do curso | `curso.titulo` |
| Situação do curso | `curso.ativo` / `curso.situacao` |
| Curso aceita pré-inscrição | `curso.aceita_pre_inscricao` |
| Identificador da turma | `turma.id` |
| Nome da turma | `turma.nome` |
| Curso da turma | `turma.curso` / `turma.curso_id` |
| Horário | `turma.hora_inicio`, `turma.hora_fim`, `turma.horario_formatado` |
| Dias e período | `turma.dias_semana`, `turma.data_inicio`, `turma.data_fim` |
| Situação da turma | `turma.ativo` / `turma.situacao` |
| Disponibilidade | `turma.vagas_disponiveis`, `turma.tem_vagas`, `turma.disponivel` |
| Ocupação | `turma.vagas_ocupadas` |
| Vagas totais da turma | `turma.vagas` |

O contrato já existente em `app/contracts.py` continua sendo o ponto de
referência entre os módulos.

### 11.2 Regras que o módulo de inscrições deve aplicar

O módulo de cursos **expõe** a disponibilidade, mas não persiste inscrições. O
bloqueio efetivo deve ser aplicado pelo módulo de inscrições antes de criar o
registro:

1. buscar o curso e garantir que ele existe;
2. garantir que `curso.aceita_pre_inscricao` é verdadeiro;
3. se houver `turma_id`, garantir que a turma pertence ao curso;
4. garantir que `turma.ativo` é verdadeiro;
5. garantir que `turma.tem_vagas` (ou `turma.disponivel`) é verdadeiro;
6. persistir a `Inscricao` com `status = StatusInscricao.RECEBIDA`;
7. tratar concorrência: duas inscrições simultâneas podem ler a mesma
   disponibilidade. Para produção, a validação e a inserção devem ocorrer na
   mesma transação ou com bloqueio adequado.

O arquivo atual `app/blueprints/inscricoes/routes.py` é um placeholder e não
persiste dados. A implementação concreta pertence à outra integrante.

### 11.3 Pendência de integração

Enquanto o módulo de inscrições não persistir os dados, a proteção pública é:

- catálogo e detalhe escondem cursos inativos;
- detalhe esconde turmas inativas;
- links de pré-inscrição só aparecem quando há vaga.

Ainda falta a validação transacional no momento do `POST` da pré-inscrição. Isso
deve ser feito no módulo de inscrições, sem alterar as rotas administrativas de
cursos. Nenhum arquivo do módulo de inscrições foi modificado aqui.

## 12. Testes

Arquivo principal: `tests/test_cursos.py`.

Os testes cobrem:

- criação de curso gratuito e geração de slug;
- unicidade de slug;
- curso pago exigindo link externo válido;
- curso gratuito descartando link externo;
- ativação e desativação de curso;
- atualização de curso preservando slug;
- validação de descrição, valor, datas e horários;
- múltiplas turmas com horários diferentes;
- controle de vagas por turma;
- cancelamento liberando vaga;
- disponibilidade agregada de várias turmas;
- exclusão bloqueada quando há inscrições;
- catálogo somente com cursos ativos;
- busca e filtro por tipo;
- detalhe com turmas e vagas;
- turma inativa oculta no detalhe;
- cards sem pré-inscrição quando não há vagas;
- curso pago com link de compra e sem pré-inscrição;
- curso gratuito e curso pago inativo sem redirecionamento de compra;
- cadastro, edição e ações administrativas;
- proteção das rotas administrativas;
- dados expostos para integração com inscrições.

Comando:

```bash
source .venv/bin/activate
pytest
```

Resultado da última execução:

```text
66 passed
```

## 13. Como executar o projeto

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
flask --app run.py db upgrade
flask --app run.py run --debug
```

Acesse:

- página inicial: <http://127.0.0.1:5000/>
- catálogo: <http://127.0.0.1:5000/cursos>
- painel: <http://127.0.0.1:5000/admin/>

Para criar o administrador:

```bash
flask --app run.py criar-admin
```

## 14. Roteiro rápido de estudo

1. Leia `app/models/curso.py` e `app/models/turma.py`.
2. Entenda as propriedades de vagas: `vagas_ocupadas`, `vagas_disponiveis`,
   `tem_vagas`, `disponivel` e `possui_vagas`.
3. Leia `app/services/curso_service.py`, começando por `criar_curso`,
   `atualizar_curso`, `criar_turma` e `_slug_unico`.
4. Leia `app/forms/curso.py` para entender a validação de entrada.
5. Siga uma requisição pública em `app/blueprints/catalogo/routes.py`.
6. Siga uma requisição administrativa em `app/blueprints/admin/routes.py`.
7. Compare as variáveis passadas pelas rotas com o uso nos templates.
8. Leia `tests/test_cursos.py` para ver as regras em execução.

## 15. Pendências e limites do módulo

- A persistência de pré-inscrições ainda é placeholder e pertence à outra
  integrante.
- O bloqueio transacional de vagas no `POST` de inscrição depende do módulo de
  inscrições.
- Login/logout e análise de inscrições também pertencem ao outro módulo.
- O módulo não usa dados reais de alunos; todos os exemplos e testes usam dados
  fictícios.
