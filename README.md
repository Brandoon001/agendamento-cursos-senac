# SENAC Sobral — Cursos Gratuitos

Aplicação Flask para divulgação dos **cursos gratuitos do SENAC em Sobral**, com
pré-inscrição interna analisada pelo administrador.

Não há cursos pagos no catálogo nem no painel administrativo. Para outras
oportunidades, a interface oferece apenas um link externo para o portal oficial
de cursos do Ceará: https://cursos.ce.senac.br/.

O sistema possui um único administrador. Este repositório contém a aplicação
completa: catálogo filtrado por cidade, turmas, controle de vagas,
pré-inscrição, autenticação, painel administrativo e exportação das inscrições
em planilha Excel.

## Escopo atual

Já implementado:

- Application Factory (`create_app`);
- configurações por ambiente e leitura de `.env`;
- extensões compartilhadas: SQLAlchemy, Migrate, Login e CSRF;
- modelos `Curso`, `Turma`, `Inscricao` e `Administrador` com relacionamentos e
  restrições básicas;
- registro central dos Blueprints;
- templates base, tratamento de erros e arquivos estáticos;
- comando CLI para criação do único administrador;
- migrações do banco;
- catálogo público com busca, filtros, página inicial e detalhe do curso;
- cadastro, edição, ativação, desativação e exclusão de cursos;
- cadastro e gerenciamento de turmas com horários e vagas diferentes;
- controle de vagas por turma, desconsiderando inscrições canceladas;
- formulário público de pré-inscrição com validação de CPF, turma, vagas e aceite
  de tratamento de dados;
- página de confirmação com protocolo;
- login e logout do administrador, com limite de tentativas via hash de senha e
  proteção contra redirecionamento externo;
- listagem, filtros e alteração de situação das inscrições no painel;
- exportação das inscrições filtradas para `.xlsx` (`openpyxl`);
- comando `seed-demo` com dados fictícios para demonstração;
- 87 testes automatizados cobrindo todos os módulos.

## Requisitos

- Python 3.10 ou superior;
- `pip` e ambiente virtual;
- SQLite (padrão) ou outro banco compatível com SQLAlchemy.

## Estrutura do projeto

```text
.
├── app/
│   ├── __init__.py              # Application Factory
│   ├── cli.py                   # Comando criar-admin
│   ├── config.py                # Configurações por ambiente
│   ├── contracts.py             # Contratos entre os módulos
│   ├── errors.py                # Tratadores de erro
│   ├── extensions.py            # SQLAlchemy, Migrate, Login e CSRF
│   ├── blueprints/
│   │   ├── __init__.py          # Registro central dos Blueprints
│   │   ├── main/                # Página inicial
│   │   ├── catalogo/            # Módulo de catálogo
│   │   ├── inscricoes/          # Módulo de pré-inscrições
│   │   ├── auth/                # Autenticação administrativa
│   │   └── admin/               # Painel administrativo
│   ├── models/
│   │   ├── base.py              # TimestampMixin
│   │   ├── enums.py             # TipoCurso e StatusInscricao
│   │   ├── curso.py
│   │   ├── turma.py             # Turmas, horários e vagas
│   │   ├── inscricao.py
│   │   └── administrador.py
│   ├── services/                # Regras de negócio (curso_service.py etc.)
│   ├── forms/                   # Formulários WTForms dos módulos
│   ├── static/
│   │   ├── css/style.css
│   │   ├── js/main.js
│   │   └── img/
│   └── templates/
│       ├── base.html
│       ├── components/
│       ├── main/
│       ├── catalogo/
│       ├── inscricoes/
│       ├── auth/
│       ├── admin/
│       └── errors/
├── legacy/                      # Scripts antigos, fora da aplicação Flask
├── migrations/                  # Migrações do banco
├── instance/                    # Banco SQLite e arquivos locais
├── tests/
├── .env.example
├── requirements.txt
├── requirements-dev.txt
├── run.py
└── wsgi.py
```

A pasta `legacy/` preserva os scripts de coleta anteriores. Ela não é importada
pela aplicação, não faz parte da fundação e pode ser removida se não for útil.

## Instalação

### Linux/macOS

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

### Windows (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Gere uma chave secreta e substitua o valor de `SECRET_KEY` no `.env`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

O arquivo `.env` não deve ser versionado. O `.env.example` contém apenas valores
de exemplo.

## Banco de dados

O projeto inclui as migrações da fundação e do módulo de cursos. Para criar o
banco local:

```bash
flask --app run.py db upgrade
```

Se a pasta `migrations/` for removida e precisar ser recriada:

```bash
flask --app run.py db init
flask --app run.py db migrate -m "estrutura inicial"
flask --app run.py db upgrade
```

Por padrão, o SQLite é criado em `instance/senac_cursos.db`. Para usar outro
banco, ajuste `DATABASE_URL` no `.env`.

## Criar o administrador

O sistema aceita somente um administrador. O comando abaixo solicita nome,
e-mail e senha e recusa a criação se já existir um registro:

```bash
flask --app run.py criar-admin
```

As senhas são armazenadas como hash pelo `werkzeug.security`; nunca são salvas
em texto puro.

Para popular o banco com dados fictícios de demonstração (3 cursos gratuitos em
Sobral e um administrador `admin@senac.br` / `senac123`):

```bash
flask --app run.py seed-demo
```

O comando é idempotente: cursos já existentes são ignorados. Use apenas em
ambiente local e troque a senha antes de publicar a aplicação.

## Execução

```bash
flask --app run.py run --debug
```

Ou:

```bash
python run.py
```

Acesse <http://127.0.0.1:5000>.

## Testes

```bash
python -m pip install -r requirements-dev.txt
pytest
```

Os testes usam um banco SQLite em memória e dados totalmente fictícios.

## Arquitetura e contratos de integração

### Application Factory

`app/__init__.py` expõe `create_app(config_name=None)`. Ele carrega a
configuração, inicializa as extensões, importa os modelos, registra os
Blueprints, os tratadores de erro e o comando CLI.

```python
from app import create_app

app = create_app("testing")
```

### Configuração

`app/config.py` define `DevelopmentConfig`, `TestingConfig` e
`ProductionConfig`. O ambiente é escolhido por `FLASK_CONFIG` (`development`,
`testing` ou `production`).

### Extensões compartilhadas

`app/extensions.py` cria instâncias únicas de:

- `db` (`Flask-SQLAlchemy`);
- `migrate` (`Flask-Migrate`);
- `login_manager` (`Flask-Login`);
- `csrf` (`Flask-WTF`).

O Blueprint `auth` é o `login_view` configurado. O Blueprint `admin` já aplica
`login_required` em todas as suas rotas por meio de `before_request`.

### Modelos

| Modelo | Tabela | Responsabilidade |
| --- | --- | --- |
| `Curso` | `cursos` | Curso gratuito, cidade e dados de divulgação. |
| `Turma` | `turmas` | Horário, período e vagas de uma oferta do curso. |
| `Inscricao` | `inscricoes` | Pré-inscrição em curso gratuito, com status e responsável. |
| `Administrador` | `administradores` | Único usuário administrativo autenticável. |

Regras refletidas no banco:

- `Curso.cidade` é obrigatória e usa `Sobral` como padrão;
- todo curso criado pelo painel é gratuito, sem valor ou link externo próprio;
- vagas e carga horária não podem ser negativas;
- a data final não pode ser anterior à data inicial;
- um curso pode ter várias turmas, cada uma com dias, horários e vagas
  próprios;
- `Inscricao.turma_id` é opcional e vinculado com `ON DELETE SET NULL`;
- CPF é obrigatório nas novas inscrições e não pode se repetir no sistema;
- curso com inscrições **não pode ser excluído**; o histórico é preservado pela
  chave estrangeira `ON DELETE RESTRICT`. Nesse caso, use `Curso.ativo = False`
  para arquivar/desativar o curso;
- turma com inscrições não deve ser excluída; use `Turma.ativo = False`;
- o controle de vagas é calculado por turma, desconsiderando inscrições com
  status `cancelada`. Turma sem quantidade de vagas definida é ilimitada.

CPF, e-mail e telefone aceitam nulos no modelo para preservar registros antigos.
O formulário e o serviço de inscrições exigem CPF válido, e a constraint
`uq_inscricoes_cpf` garante uma única inscrição por pessoa.

As enumerações `TipoCurso` (somente `GRATUITO`) e `StatusInscricao` ficam em
`app/models/enums.py`. Os status de inscrição são: `RECEBIDA`, `EM_ANALISE`,
`CONTATADA`, `FINALIZADA` e `CANCELADA`. O status inicial é `RECEBIDA`.

As configurações `CIDADE_PADRAO` e `PORTAL_CURSOS_URL` ficam em `app/config.py`
e podem ser sobrescritas por variáveis de ambiente.

### Blueprints e endpoints

| Blueprint | Prefixo | Endpoints | Responsável |
| --- | --- | --- | --- |
| `main` | `/` | `main.index` | Fundação |
| `catalogo` | `/cursos` | `catalogo.listar`, `catalogo.detalhe` | Módulo de cursos |
| `inscricoes` | `/inscricoes` | `inscricoes.pre_inscricao`, `inscricoes.confirmacao` | Módulo de inscrições |
| `auth` | `/auth` | `auth.login`, `auth.logout` | Módulo administrativo |
| `admin` | `/admin` | `admin.dashboard`, `admin.cursos`, `admin.novo_curso`, `admin.editar_curso`, `admin.ativar_curso`, `admin.desativar_curso`, `admin.excluir_curso`, `admin.turmas_do_curso`, `admin.nova_turma`, `admin.editar_turma`, `admin.ativar_turma`, `admin.desativar_turma`, `admin.excluir_turma`, `admin.inscricoes`, `admin.alterar_status_inscricao`, `admin.exportar_inscricoes` | Módulos de cursos e inscrições |

O registro é centralizado em `app/blueprints/__init__.py`. Rotas futuras devem
ser adicionadas dentro do Blueprint já existente; a fundação não precisa ser
alterada para isso.

### Contratos de serviço

`app/contracts.py` define os protocolos:

- `CatalogoService`: listagem pública de cursos gratuitos da cidade
  configurada e busca por identificador;
- `InscricaoService`: criação de pré-inscrição, listagem e alteração de status.
  O contrato **não exige controle automático de vagas**; eventuais regras de
  disponibilidade devem ser definidas explicitamente pelo módulo;
- `AutenticacaoService`: autenticação do administrador.

As implementações concretas devem ficar em `app/services/`. Os Blueprints devem
chamar os serviços, não concentrar regras de negócio em `routes.py`.

## Módulos e regras adotadas

### Módulo de cursos

Arquivos principais:

- `app/blueprints/catalogo/routes.py` e `app/blueprints/admin/routes.py`;
- `app/templates/catalogo/`, `app/templates/admin/cursos/` e
  `app/templates/components/curso_card.html`;
- `app/services/curso_service.py`;
- `app/forms/curso.py`;
- `app/models/curso.py` e `app/models/turma.py`.

O módulo já oferece:

1. Página inicial e catálogo público somente com cursos ativos, gratuitos e de
   Sobral;
2. busca por nome/descrição;
3. cards reutilizáveis, detalhe do curso e layout responsivo;
4. CRUD administrativo somente de cursos gratuitos, com campo `cidade`;
5. ativação/desativação de cursos e turmas;
6. turmas com dias, horários, período e vagas próprios;
7. controle de vagas por turma, ignorando inscrições canceladas;
8. link externo único para o portal de cursos do SENAC Ceará na navbar e na
   página inicial.

Cursos gratuitos apontam para
`url_for("inscricoes.pre_inscricao", curso_id=curso.id)` e podem incluir
`turma_id` como parâmetro de consulta para que o módulo de inscrições vincule a
inscrição à turma escolhida.

### Módulo de pré-inscrições

Arquivos principais:

- `app/blueprints/inscricoes/routes.py`;
- `app/templates/inscricoes/`;
- `app/services/inscricao_service.py`;
- `app/forms/inscricao.py`.

Regras implementadas:

1. Aceite apenas cursos gratuitos, ativos e que aceitem pré-inscrição.
2. Valide o CSRF (já habilitado globalmente; use `csrf_token()` no formulário).
3. Persista `Inscricao` com status inicial `StatusInscricao.RECEBIDA`.
4. CPF é obrigatório e validado pelo formulário e pelo serviço; e-mail e
   telefone também são obrigatórios no formulário público.
5. O módulo de cursos já expõe turmas e o cálculo de vagas em
   `Turma.vagas_disponiveis`. Se a inscrição estiver vinculada a uma turma,
   valide a disponibilidade antes de persistir e associe `Inscricao.turma`.
6. Trate `IntegrityError` para CPF duplicado em qualquer curso; o serviço
   normaliza a máscara antes de consultar e gravar.
7. Nunca use dados reais de alunos em exemplos, testes ou seeds;
8. o protocolo exibido na confirmação tem o formato `INS-ANO-00001`;
9. a confirmação só pode ser vista pela sessão que criou a inscrição (ou pelo
   administrador).

### Módulo administrativo e autenticação

Arquivos principais:

- `app/blueprints/auth/routes.py`;
- `app/blueprints/admin/routes.py`;
- `app/templates/auth/`, `app/templates/admin/` e
  `app/templates/admin/inscricoes.html`;
- `app/services/autenticacao_service.py`;
- `app/services/exportacao_service.py`.

Regras implementadas:

1. Implemente `login` com `Administrador.verificar_senha` e `login_user`.
2. Implemente `logout` com `logout_user`.
3. Mantenha o `before_request` do Blueprint `admin`; novas rotas já ficam
   protegidas automaticamente.
4. O link de login não aparece na navegação pública. O acesso administrativo é
   feito diretamente em `/auth/login` por quem já conhece o endereço.
5. Use `flask --app run.py criar-admin` para criar o único administrador.
6. Alterações de status registram `administrador_id` na inscrição;
7. ao gerenciar cursos com inscrições, **arquive** (`ativo = False`) em vez de
   excluir. A exclusão é bloqueada pelo banco para preservar o histórico;
8. `/admin/inscricoes` filtra por nome/CPF/e-mail, situação e curso;
9. `/admin/inscricoes/exportar` gera um `.xlsx` com exatamente o mesmo filtro da
   tela, incluindo protocolo, contato, turma, situação e observações.

### Alterações no banco

Se um módulo precisar de novos campos, altere o modelo correspondente e gere
uma nova migração:

```bash
flask --app run.py db migrate -m "descrição da alteração"
flask --app run.py db upgrade
```

Não edite arquivos já aplicados em `migrations/versions/` sem necessidade.
Mantenha as mudanças de esquema pequenas e compatíveis com os demais módulos.
A migração `b7c1d2e3f4a5` já aplica as revisões de status, campos opcionais e
preservação do histórico; a migração `c3d4e5f6a7b8` cria as turmas e o vínculo
opcional `inscricoes.turma_id`. A migração `f6a7b8c9d0e1` adiciona
`cursos.cidade` (padrão `Sobral`) e exclui cursos pagos e seu histórico. A
migração `a2b3c4d5e6f7` substitui a unicidade de CPF por curso pela unicidade
global, normalizando CPFs antigos para `000.000.000-00` e mantendo apenas a
inscrição mais antiga de cada CPF. Migrações anteriores não devem ser apagadas.
A `b7c1d2e3f4a5` converte os status antigos assim: `pendente` → `recebida`,
`lista_espera` → `em_analise`, `confirmada` → `finalizada` e `cancelada` →
`cancelada`.

Se precisar reverter apenas a última revisão:

```bash
flask --app run.py db downgrade f6a7b8c9d0e1
```

O downgrade restaura a constraint por curso. Um downgrade até `c3d4e5f6a7b8`
remove a coluna `cidade`. Os cursos pagos excluídos pela migração
`f6a7b8c9d0e1` não podem ser restaurados.

## Regras para integração

- Não importe nada da pasta `legacy/` nem de repositórios externos.
- Não crie um segundo administrador; o comando CLI já impõe essa regra.
- Todos os cursos são gratuitos e pertencem a uma cidade; o catálogo público
  mostra apenas os cursos de `CIDADE_PADRAO` (Sobral).
- Não recrie campos ou rotas de compra. O único direcionamento externo é o link
  único para https://cursos.ce.senac.br/.
- Pré-inscrição é exclusiva para cursos ativos da cidade configurada.
- Cursos com inscrições não devem ser excluídos; use `ativo = False` para
  arquivar. O banco bloqueia a exclusão para preservar o histórico.
- Turmas com inscrições também não devem ser excluídas; use
  `Turma.ativo = False`.
- O controle de vagas é feito por turma por meio de `Turma.vagas` e das
  propriedades `vagas_ocupadas`, `vagas_disponiveis`, `tem_vagas` e
  `disponivel`. Inscrições canceladas não ocupam vaga.
- Mantenha os nomes de endpoints existentes para não quebrar `url_for`.
- Prefira estender templates e Blueprints existentes a modificar a fundação.
- Nunca versione `.env`, banco local ou dados reais de alunos.

## Segurança

- Gere um `SECRET_KEY` exclusivo para cada ambiente.
- Mantenha `WTF_CSRF_ENABLED=True` fora dos testes.
- Em produção, use HTTPS, `FLASK_CONFIG=production` e um servidor WSGI
  (por exemplo, Gunicorn) apontando para `wsgi:app`.
- O projeto não inclui dados reais de alunos.
# agendamento-cursos-senac
