# Manutenção

## Objetivo

Centralizar deploy, backup, diagnóstico, dívida técnica e checklist de mudanças. Veja também [Configuração](CONFIGURACAO.md), [Banco de dados](BANCO_DE_DADOS.md), [Segurança](SEGURANCA.md) e [Testes](TESTES.md).

## Diagnóstico rápido

| Sintoma | Verificação | Ação |
| --- | --- | --- |
| `500` ao abrir página | logs da aplicação | handler faz rollback e `logger.exception`; corrigir causa raiz |
| `CSRF error 400` | formulário sem token | usar `form.hidden_tag()` ou `csrf_token()` |
| Admin redireciona para login | sessão ausente/inválida | entrar em `/auth/login`; verificar `SECRET_KEY` |
| Curso não aparece no catálogo | filtro de visibilidade | ativo, `gratuito` e `CIDADE_PADRAO` |
| Inscrição duplicada rejeitada | CPF único global | usar outro CPF ou localizar registro existente |
| Exclusão recusada | inscrições vinculadas | desativar curso/turma |
| Gráfico do dashboard estranho | `.chart-box` e Chart.js | manter container com altura fixa |
| Cards com muitas linhas em branco | whitespace Jinja | usar `{%- ... -%}` |
| Login em produção falha ao iniciar | `SECRET_KEY` placeholder | gerar chave aleatória |
| Upload falha | extensão, assinatura ou 4 MB | verificar arquivo e `MAX_CONTENT_LENGTH` |

## Logs

Erros 500 são registrados por `app/errors.py:26-30` com:

```python
current_app.logger.exception("Erro não tratado", exc_info=erro)
```

Configure o handler de logging do servidor WSGI/proxy para persistir stderr. Não há logging estruturado nem correlação de requisições.

Falhas de login não são logadas atualmente; veja [Segurança](SEGURANCA.md).

## Backup

### SQLite

```bash
cp instance/senac_cursos.db instance/senac_cursos.db.bak
```

Antes de restore, pare a aplicação. Se WAL estiver ativo, inclua `instance/senac_cursos.db-wal` e `-shm`.

### Uploads

```bash
cp -r app/static/uploads app/static/uploads.bak
```

Imagens referenciadas por `Curso.imagem_url` ficam em `app/static/uploads/`.

### Restore

1. Parar aplicação.
2. Restaurar banco e uploads.
3. Confirmar `flask db current`.
4. Reiniciar.
5. Validar rotas públicas e login.

## Deploy

Checklist:

1. `FLASK_CONFIG=production`.
2. `SECRET_KEY` aleatória e secreta.
3. `DATABASE_URL` correto.
4. `flask --app run.py db upgrade`.
5. Admin criado; `seed-demo` não executado.
6. HTTPS e cookies Secure.
7. `wsgi:app` no servidor WSGI.
8. Cabeçalhos de segurança no proxy.
9. Permissão de escrita em `instance/` e `app/static/uploads/`.
10. Backup recente.
11. Testes locais passando.
12. `git diff --check` limpo.

Subida de nova versão com schema:

```bash
git pull
python -m pip install -r requirements.txt
flask --app run.py db upgrade
sudo systemctl restart agenda-senac
```

Ajuste o nome do serviço conforme o ambiente.

## Validação pós-deploy

```bash
curl -I https://<host>/
curl -I https://<host>/cursos
curl -I https://<host>/auth/login
flask --app run.py db current
```

Verifique também:

- catálogo mostra cursos da cidade configurada;
- login funciona;
- painel carrega cards e gráfico;
- exportação baixa XLSX;
- upload de imagem salva e exibe;
- comprovante abre para a sessão correta.

## Dívida técnica e melhorias sugeridas

| Item | Documento | Prioridade |
| --- | --- | --- |
| Rate limiting de login | [Segurança](SEGURANCA.md) | alta |
| Corrida pela última vaga | [Segurança](SEGURANCA.md) | alta |
| Cabeçalhos de segurança/CSP | [Segurança](SEGURANCA.md) | alta |
| Unicidade do admin no banco | [Banco de dados](BANCO_DE_DADOS.md) | média |
| Drift `ix_cursos_publicacao` × `ix_cursos_cidade` | [Banco de dados](BANCO_DE_DADOS.md) | média |
| Constraint legada aceitando `pago` | [Banco de dados](BANCO_DE_DADOS.md) | média |
| Paginação de listagens | [Banco de dados](BANCO_DE_DADOS.md) | média |
| Datas fixas no `seed-demo` | [CLI](CLI.md) | baixa |
| Audit log de alterações | [Segurança](SEGURANCA.md) | média |
| Testes com CSRF ligado | [Testes](TESTES.md) | média |
| Lint/typecheck não configurados | [Testes](TESTES.md) | baixa |

## Checklist de mudança

Antes de commitar:

- [ ] regra alterada também refletida em `docs/`;
- [ ] modelo alterado → migração criada;
- [ ] rota nova → [Rotas](ROTAS.md) atualizado;
- [ ] formulário novo → [Formulários](FORMULARIOS.md) atualizado;
- [ ] serviço novo → [Serviços](SERVICOS.md) atualizado;
- [ ] teste escrito/atualizado;
- [ ] `.venv/bin/python -m pytest -q`;
- [ ] `git diff --check`;
- [ ] nenhum dado real ou segredo versionado.

## Convenções de código

- Rotas finas: regras ficam em `app/services/`.
- Formulários apenas validam entrada; não persistem.
- Modelos expõem propriedades de domínio quando faz sentido.
- Templates usam componentes de `app/templates/components/`.
- Mensagens ao usuário em português.
- Erros de serviço usam `ValueError` com texto amigável.
- Nunca versionar `.env`, banco local ou uploads de produção.

## Leitura complementar

- [Índice](INDICE.md)
- [Arquitetura](ARQUITETURA.md)
- [Configuração](CONFIGURACAO.md)
- [Segurança](SEGURANCA.md)
