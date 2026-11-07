# SENAC Cursos

Aplicação Flask para divulgação de cursos do SENAC, com dois fluxos:

- **cursos pagos**: direcionamento para um link externo individual de compra;
- **cursos gratuitos**: pré-inscrição interna, analisada pelo administrador.

O sistema possui um único administrador. Este repositório contém **apenas a
fundação compartilhada**; as regras de catálogo, pré-inscrição e painel
administrativo serão implementadas pelos integrantes da equipe.

## Escopo da fundação

Já implementado:

- Application Factory (`create_app`);
- configurações por ambiente e leitura de `.env`;
- extensões compartilhadas: SQLAlchemy, Migrate, Login e CSRF;
- modelos `Curso`, `Inscricao` e `Administrador` com relacionamentos e
  restrições básicas;
- registro central dos Blueprints;
- templates base, tratamento de erros e arquivos estáticos;
- comando CLI para criação do único administrador;
- migração inicial do banco;
- testes automatizados da fundação.

Não implementado nesta etapa:

- consulta e exibição real de cursos;
- formulário e persistência de pré-inscrições;
- login, logout e painel administrativo completos;
- CRUD de cursos.

As rotas existentes nesses módulos são placeholders documentados e devem ser
substituídas pelas implementações dos responsáveis.

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
│   │   ├── inscricao.py
│   │   └── administrador.py
│   ├── services/                # Implementações dos contratos de negócio
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

O projeto inclui a migração inicial. Para criar o banco local:

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
| `Curso` | `cursos` | Curso pago ou gratuito, dados de divulgação e link externo. |
| `Inscricao` | `inscricoes` | Pré-inscrição em curso gratuito, com status e responsável. |
| `Administrador` | `administradores` | Único usuário administrativo autenticável. |

Regras refletidas no banco:

- `Curso.tipo` aceita somente `pago` ou `gratuito`;
- curso pago exige `link_externo`; curso gratuito não pode ter link externo;
- valores, vagas e carga horária não podem ser negativos;
- a data final não pode ser anterior à data inicial;
- quando informado, o CPF não pode se repetir no mesmo curso;
- curso com inscrições **não pode ser excluído**; o histórico é preservado pela
  chave estrangeira `ON DELETE RESTRICT`. Nesse caso, use `Curso.ativo = False`
  para arquivar/desativar o curso;
- `Curso.vagas` é apenas informativo nesta fundação: não existe controle
  automático de vagas, lista de espera ou reserva.

CPF, e-mail e telefone são opcionais no modelo. A obrigatoriedade desses campos
deve ser definida posteriormente pelo módulo de inscrições, sem exigir mudança
estrutural na fundação.

As enumerações `TipoCurso` e `StatusInscricao` ficam em
`app/models/enums.py`. Os status de inscrição são: `RECEBIDA`, `EM_ANALISE`,
`CONTATADA`, `FINALIZADA` e `CANCELADA`. O status inicial é `RECEBIDA`.

### Blueprints e endpoints

| Blueprint | Prefixo | Endpoints | Responsável |
| --- | --- | --- | --- |
| `main` | `/` | `main.index` | Fundação |
| `catalogo` | `/cursos` | `catalogo.listar`, `catalogo.detalhe` | Módulo de catálogo |
| `inscricoes` | `/inscricoes` | `inscricoes.pre_inscricao`, `inscricoes.confirmacao` | Módulo de inscrições |
| `auth` | `/auth` | `auth.login`, `auth.logout` | Módulo administrativo |
| `admin` | `/admin` | `admin.dashboard` | Módulo administrativo |

O registro é centralizado em `app/blueprints/__init__.py`. Rotas futuras devem
ser adicionadas dentro do Blueprint já existente; a fundação não precisa ser
alterada para isso.

### Contratos de serviço

`app/contracts.py` define os protocolos:

- `CatalogoService`: listagem pública, busca por identificador e obtenção do
  link de compra;
- `InscricaoService`: criação de pré-inscrição, listagem e alteração de status.
  O contrato **não exige controle automático de vagas**; eventuais regras de
  disponibilidade devem ser definidas explicitamente pelo módulo;
- `AutenticacaoService`: autenticação do administrador.

As implementações concretas devem ficar em `app/services/`. Os Blueprints devem
chamar os serviços, não concentrar regras de negócio em `routes.py`.

## Como implementar cada módulo

### Módulo de catálogo e cursos pagos

Arquivos principais:

- `app/blueprints/catalogo/routes.py`;
- `app/templates/catalogo/`;
- `app/services/catalogo_service.py`;
- `app/forms/` (formulários administrativos, se necessário).

Orientações:

1. Use o modelo `Curso` e filtre por `ativo`.
2. Para `Curso.tipo == TipoCurso.PAGO`, redirecione para
   `Curso.link_externo`.
3. Para `Curso.tipo == TipoCurso.GRATUITO`, aponte para
   `url_for("inscricoes.pre_inscricao", curso_id=curso.id)`.
4. Reaproveite `base.html` e os blocos Jinja existentes.
5. Não altere o Application Factory nem os modelos sem necessidade.

### Módulo de pré-inscrições

Arquivos principais:

- `app/blueprints/inscricoes/routes.py`;
- `app/templates/inscricoes/`;
- `app/services/inscricao_service.py`;
- `app/forms/inscricao.py`.

Orientações:

1. Aceite apenas cursos gratuitos, ativos e que aceitem pré-inscrição.
2. Valide o CSRF (já habilitado globalmente; use `csrf_token()` no formulário).
3. Persista `Inscricao` com status inicial `StatusInscricao.RECEBIDA`.
4. Defina a obrigatoriedade de CPF, e-mail e telefone na validação do módulo;
   o modelo aceita esses campos nulos.
5. Não implemente controle automático de vagas por conta própria: o contrato
   `InscricaoService` não exige essa regra. Se ela for necessária, deve ser
   especificada e implementada explicitamente.
6. Trate `IntegrityError` para CPF duplicado no mesmo curso quando o CPF for
   informado.
7. Nunca use dados reais de alunos em exemplos, testes ou seeds.

### Módulo administrativo e autenticação

Arquivos principais:

- `app/blueprints/auth/routes.py`;
- `app/blueprints/admin/routes.py`;
- `app/templates/auth/` e `app/templates/admin/`;
- `app/services/autenticacao_service.py`.

Orientações:

1. Implemente `login` com `Administrador.verificar_senha` e `login_user`.
2. Implemente `logout` com `logout_user`.
3. Mantenha o `before_request` do Blueprint `admin`; novas rotas já ficam
   protegidas automaticamente.
4. Use `flask --app run.py criar-admin` para criar o único administrador.
5. Alterações de status devem registrar `administrador_id` na inscrição.
6. Ao gerenciar cursos com inscrições, **arquive** (`ativo = False`) em vez de
   excluir. A exclusão é bloqueada pelo banco para preservar o histórico.

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
preservação do histórico; migrações anteriores não devem ser apagadas. Ela
converte os status antigos assim: `pendente` → `recebida`, `lista_espera` →
`em_analise`, `confirmada` → `finalizada` e `cancelada` → `cancelada`.

Se precisar reverter apenas a última revisão:

```bash
flask --app run.py db downgrade e20f62e9afcd
```

O downgrade preenche CPF/e-mail nulos com marcadores técnicos para restaurar o
schema antigo. Esses valores não representam dados reais.

## Regras para integração

- Não importe nada da pasta `legacy/` nem de repositórios externos.
- Não crie um segundo administrador; o comando CLI já impõe essa regra.
- Curso pago deve ter link externo individual; curso gratuito não deve ter.
- Pré-inscrição é exclusiva para cursos gratuitos.
- Cursos com inscrições não devem ser excluídos; use `ativo = False` para
  arquivar. O banco bloqueia a exclusão para preservar o histórico.
- Não presuma controle automático de vagas; o contrato atual não exige essa
  regra.
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
