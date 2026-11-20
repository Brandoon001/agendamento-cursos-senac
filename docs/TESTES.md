# Testes

## Objetivo

Documentar como rodar, entender e estender a suíte automatizada. Veja também [Configuração](CONFIGURACAO.md), [Segurança](SEGURANCA.md) e [Manutenção](MANUTENCAO.md).

## Comando principal

```bash
python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
```

Estado atual: **103 testes passando**.

Também funciona:

```bash
pytest
python -m pytest
```

Use `.venv/bin/python -m pytest -q` para garantir que está no interpretador do ambiente virtual.

## Ambiente de teste

`app/config.py` define `TestingConfig`:

| Configuração | Valor |
| --- | --- |
| `TESTING` | `True` |
| `DEBUG` | `False` |
| `SQLALCHEMY_DATABASE_URI` | `sqlite:///:memory:` |
| `WTF_CSRF_ENABLED` | `False` |
| `SECRET_KEY` | `chave-exclusiva-de-testes` |

Nenhum dado real é usado. O banco é criado e destruído por teste.

## Fixtures

Definidas em `tests/conftest.py`:

| Fixture | Finalidade |
| --- | --- |
| `app` | `create_app("testing")`, `db.create_all()`, `session_protection=None`, drop no teardown |
| `client` | `app.test_client()` |
| `administrador` | cria admin fictício `admin@example.com` / `senha-ficticia` |
| `client_autenticado` | client com sessão Flask-Login preenchida |

`login_manager.session_protection = None` evita que mudanças de IP/user-agent invalidem a sessão no cliente de teste.

## Arquivos

| Arquivo | Escopo provável |
| --- | --- |
| `tests/test_app_factory.py` | configurações, extensões, handlers, CLI registration |
| `tests/test_models.py` | propriedades de `Curso`, `Turma`, `Inscricao`, enums e hashes |
| `tests/test_auth.py` | login, logout, redirect seguro, admin inativo |
| `tests/test_cursos.py` | catálogo, CRUD, slug, ativação, turmas, visibilidade |
| `tests/test_inscricoes.py` | CPF, duplicidade, turma, vagas, status, comprovante, exportação |
| `tests/test_upload_imagem.py` | extensões, assinaturas, tamanho, remoção |
| `tests/test_cli.py` | `criar-admin`, `seed-demo` e idempotência |
| `tests/test_admin_ui.py` | regressão do loop de situações e do gráfico do dashboard |

Para confirmar a contagem por arquivo:

```bash
rg -c '^(def test_|    def test_)' tests
```

## Convenções para novos testes

1. Use `client` para rotas públicas e `client_autenticado` para `/admin/*`.
2. Crie dados com `db.session.add()`/`commit()` dentro do contexto da fixture `app`.
3. Use nomes e CPFs fictícios.
4. Para POSTs, lembre que CSRF está desligado em `TestingConfig`.
5. Para testar `ValueError` de serviço, chame o serviço diretamente ou verifique o flash na rota.
6. Para mudanças de template, afirme trechos do HTML com `response.get_data(as_text=True)`.

Exemplo:

```python
def test_lista_inscricoes_sem_linhas_extras(client_autenticado):
    resposta = client_autenticado.get("/admin/inscricoes")
    html = resposta.get_data(as_text=True)
    assert "Pré-inscrições" in html
    assert html.count("stat-card") >= 5
```

## Testes de regressão importantes

- **Cards de situação:** `contar_por_status()` deve incluir os cinco status com zero; `admin/dashboard.html` e `admin/inscricoes.html` não devem produzir blocos vazios extras.
- **Gráfico:** canvas deve estar dentro de `.chart-box` e Chart.js carregado apenas no dashboard.
- **Exportação:** valores começando com `=`, `+`, `-` ou `@` precisam ser texto no XLSX.
- **CPF:** duplicidade global deve gerar erro amigável.
- **Comprovante:** ID fora da sessão e sem admin retorna `404`.

## Smoke test manual

Durante a modernização foi usado um script temporário fora do repositório:

```bash
PYTHONPATH=. .venv/bin/python /tmp/opencode/smoke_agenda_senac.py
```

Ele verifica rotas, filtros, campos, CSRF, CDNs e ausência de jQuery/duplicação de Bootstrap CSS. Como está em `/tmp`, **não é parte da suíte versionada**. Se quiser preservá-lo, mova para `tests/` e adapte às fixtures.

## Validação adicional

```bash
git diff --check
```

Não há lint configurado (`ruff`, `flake8`, `black`, `mypy`). Se algum for adicionado, documente aqui.

## Lacunas de cobertura

- token CSRF com `WTF_CSRF_ENABLED=True`;
- concorrência na última vaga;
- cabeçalhos de segurança;
- rate limiting de login;
- errors 400/403/404/500 em todas as rotas;
- upload com arquivo corrompido que passa pela assinatura;
- paginação (recurso ainda não existe).

## Leitura complementar

- [Configuração](CONFIGURACAO.md)
- [Segurança](SEGURANCA.md)
- [Manutenção](MANUTENCAO.md)
