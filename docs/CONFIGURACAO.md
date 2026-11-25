# Configuração

## Objetivo

Documentar variáveis de ambiente, classes de configuração e ajustes necessários para desenvolvimento, testes e produção. Veja também [Arquitetura](ARQUITETURA.md) e [Segurança](SEGURANCA.md).

## Carregamento de `.env`

`app/config.py:19` chama `load_dotenv(BASE_DIR / ".env")` durante o import do módulo.

- Variáveis já presentes no ambiente têm precedência sobre o `.env`.
- `.env` não deve ser versionado.
- Use `.env.example` como referência.
- `FLASK_APP` e `FLASK_DEBUG` são lidas pelo CLI do Flask, não pelas classes de configuração.

## Variáveis suportadas

| Variável | Uso | Padrão | Obrigatória em produção? |
| --- | --- | --- | --- |
| `FLASK_CONFIG` | Seleciona a classe de configuração | `development` no `run.py`; `production` no `wsgi.py` | Recomendado definir explicitamente |
| `FLASK_APP` | Entrypoint do CLI Flask | `run.py` no exemplo | Não |
| `FLASK_DEBUG` | Ativa debug no CLI | `1` no exemplo | Não; deve ser `0` |
| `SECRET_KEY` | Assina sessões e tokens CSRF | `dev-apenas-troque-esta-chave` | **Sim** |
| `DATABASE_URL` | URI SQLAlchemy | `sqlite:///<instance>/senac_cursos.db` | Não |
| `WTF_CSRF_TIME_LIMIT` | Validade do token CSRF em segundos | `3600` | Não |
| `CIDADE_PADRAO` | Cidade usada no catálogo e em novos cursos | `Sobral` | Não |
| `PORTAL_CURSOS_URL` | Único link externo exibido | `https://cursos.ce.senac.br/` | Não |

`DATABASE_URL` com prefixo `postgres://` é normalizado para `postgresql://` (`app/config.py:22-26`).

## Classes de configuração

Definidas em `app/config.py`.

| Classe | Quando | Características |
| --- | --- | --- |
| `Config` | base | CSRF ligado, cookies HttpOnly/SameSite=Lax, upload 4 MB, cidade padrão |
| `DevelopmentConfig` | `development` / `dev` | `DEBUG=True` |
| `TestingConfig` | `testing` / `test` | SQLite `:memory:`, CSRF desligado, chave exclusiva de testes |
| `ProductionConfig` | `production` / `prod` | `DEBUG=False`, cookies Secure |

`get_config()` aceita `development`, `dev`, `testing`, `test`, `production` e `prod`, com `.strip().lower()`. Qualquer outro valor gera `ValueError("Configuração desconhecida: ...")`.

### Valores importantes da base

| Config | Valor |
| --- | --- |
| `SESSION_COOKIE_HTTPONLY` | `True` |
| `SESSION_COOKIE_SAMESITE` | `"Lax"` |
| `REMEMBER_COOKIE_HTTPONLY` | `True` |
| `WTF_CSRF_ENABLED` | `True` |
| `WTF_CSRF_TIME_LIMIT` | `3600` |
| `MAX_CONTENT_LENGTH` | `4 * 1024 * 1024` |
| `UPLOAD_FOLDER` | `app/static/uploads` |
| `UPLOAD_URL_PREFIX` | `/static/uploads/` |
| `UPLOAD_EXTENSOES_IMAGEM` | `png`, `jpg`, `jpeg`, `gif`, `webp` |

Duração da sessão permanece no padrão Flask de 31 dias; não há `PERMANENT_SESSION_LIFETIME` explícito.

## Ambientes

### Desenvolvimento

```bash
cp .env.example .env
flask --app run.py db upgrade
flask --app run.py criar-admin
flask --app run.py run --debug
```

`run.py` chama `create_app()`; portanto, se `FLASK_CONFIG` estiver ausente, o padrão é `development`.

### Testes

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

`TestingConfig` usa SQLite em memória e desabilita CSRF. Isso torna os testes rápidos, mas significa que eles não verificam tokens CSRF; veja [Testes](TESTES.md) e [Segurança](SEGURANCA.md).

### Produção

`wsgi.py:7` usa:

```python
app = create_app(os.getenv("FLASK_CONFIG", "production"))
```

Isso evita que um deploy sem `FLASK_CONFIG` rode com debug e chave fraca. Como `ProductionConfig` exige uma `SECRET_KEY` segura, importar `wsgi:app` sem `SECRET_KEY` configurada falha rapidamente.

Exemplo de `.env` para produção:

```dotenv
FLASK_CONFIG=production
FLASK_DEBUG=0
SECRET_KEY=<gerar-com-python-secrets-token-urlsafe-32>
DATABASE_URL=sqlite:////caminho/absoluto/senac_cursos.db
WTF_CSRF_TIME_LIMIT=3600
CIDADE_PADRAO=Sobral
PORTAL_CURSOS_URL=https://cursos.ce.senac.br/
```

Gerando uma chave:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Para SQLite, use caminho absoluto com quatro barras após `sqlite:` no `DATABASE_URL`.

## Validação de produção

`app/__init__.py:27-31` bloqueia a inicialização se a configuração resolvida for `ProductionConfig` e `SECRET_KEY` for:

- `dev-apenas-troque-esta-chave`
- `troque-esta-chave-por-um-valor-aleatorio-seguro`

## Configuração e comportamento

| Configuração | Efeito observável |
| --- | --- |
| `CIDADE_PADRAO` | Define o filtro do catálogo (`CursoService.listar_cursos_publicos`) e o valor inicial do formulário de novo curso |
| `PORTAL_CURSOS_URL` | Link externo único exibido na navbar pública |
| `MAX_CONTENT_LENGTH` | Limite de upload e tamanho máximo aceito por `UploadImagemService` |
| `WTF_CSRF_TIME_LIMIT` | Tempo de validade do token |
| `SESSION_COOKIE_SECURE` | `True` somente em produção; exige HTTPS |

`Sobral` também aparece como valor literal no modelo `Curso`, no `seed-demo` e em fixtures de teste. A configuração controla o comportamento principal, mas uma mudança completa de cidade exige revisar esses pontos.

## Checklist antes de subir

- [ ] `FLASK_CONFIG=production`
- [ ] `FLASK_DEBUG=0`
- [ ] `SECRET_KEY` aleatória e secreta
- [ ] `DATABASE_URL` apontando para o banco correto
- [ ] `flask db upgrade` executado
- [ ] HTTPS configurado no proxy/servidor
- [ ] `wsgi:app` usado pelo servidor WSGI
- [ ] Uploads com permissão de escrita e backup
- [ ] Admin criado com `criar-admin`

## Leitura complementar

- [Segurança](SEGURANCA.md)
- [Banco de dados](BANCO_DE_DADOS.md)
- [CLI](CLI.md)
- [Manutenção](MANUTENCAO.md)
