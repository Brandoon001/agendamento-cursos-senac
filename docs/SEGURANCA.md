# Segurança

## Objetivo

Documentar controles implementados, cuidados de deploy e pendências de segurança. Veja também [Configuração](CONFIGURACAO.md), [Formulários](FORMULARIOS.md) e [Manutenção](MANUTENCAO.md).

## Controles implementados

### Autenticação e sessão

| Controle | Onde | Efeito |
| --- | --- | --- |
| Hash de senha | `Administrador.definir_senha()` | `generate_password_hash` do Werkzeug |
| Comparação segura | `Administrador.verificar_senha()` | `check_password_hash` |
| E-mail normalizado | `AutenticacaoService.autenticar()` | `strip().lower()` |
| Usuário ativo | `is_active` | administradores inativos não entram |
| `session_protection = "strong"` | `app/extensions.py` | protege sessão contra mudança de identificador |
| Cookies HttpOnly/SameSite=Lax | `app/config.py` | reduz roubo por JS e CSRF |
| Cookies Secure em produção | `ProductionConfig` | exige HTTPS |
| Guard de produção | `app/__init__.py` | bloqueia `SECRET_KEY` placeholder |
| Default WSGI production | `wsgi.py` | deploy sem `FLASK_CONFIG` não cai em dev |

### Autorização

- `admin.before_request` aplica `login_required` a todas as rotas `/admin/*`.
- `inscricoes.confirmacao` só permite a sessão que criou a inscrição ou um administrador autenticado.
- Não há papéis diferentes; sistema prevê um único administrador.

### CSRF

- `CSRFProtect` inicializado globalmente.
- Todos os POSTs administrativos incluem `csrf_token()`.
- `InscricaoForm` usa `form.hidden_tag()`.
- `CSRFError` é tratado como `400` com template amigável.
- `WTF_CSRF_ENABLED=False` apenas em `TestingConfig`.

### Redirecionamentos

`auth._destino_seguro()` aceita `next` somente se:

- não possui `scheme` nem `netloc`;
- começa com `/`;
- não começa com `//` nem `/\`.

`admin._destino_admin()` aplica regra semelhante e exige prefixo `/admin/`.

### Upload de imagem

`UploadImagemService` protege contra:

- extensões não permitidas;
- arquivos vazios;
- arquivos acima de `MAX_CONTENT_LENGTH` (4 MB);
- conteúdo que não corresponda às assinaturas PNG/JPG/GIF/WebP;
- remoção de arquivos fora de `UPLOAD_URL_PREFIX`;
- traversal com `/`, `\` ou `..` no nome.

Limitações: não há reprocessamento/redimensionamento nem verificação completa de decodificação; um arquivo com cabeçalho válido e corpo inválido pode ser aceito.

### Exportação XLSX

`gerar_planilha_inscricoes()` força `data_type = "s"` para valores que começam com `=`, `+`, `-` ou `@`. Isso mitiga injeção de fórmulas em planilhas abertas pelo administrador.

### Dados

- Nenhum dado real de aluno é versionado.
- `seed-demo` usa cursos fictícios e credencial óbvia de demonstração.
- CPF é único globalmente e validado por dígitos verificadores.
- Logs de erro 500 usam `current_app.logger.exception`.

## Pendências conhecidas

| Item | Impacto | Recomendação |
| --- | --- | --- |
| Sem rate limiting em `/auth/login` | força bruta | Flask-Limiter ou limite no proxy |
| Sem CSP, HSTS, X-Content-Type-Options etc. | cabeçalhos ausentes | configurar no proxy/servidor ou extensão |
| Verificação de vaga antes do commit | corrida pela última vaga | transação com lock ou constraint atômica |
| Unicidade do admin só no CLI | segundo admin via SQL direto | constraint parcial/flag no banco |
| `SECRET_KEY` padrão em desenvolvimento | aceitável só local | nunca usar fora de dev |
| CSRF desligado em testes | não cobre tokens | teste dedicado com CSRF ligado |
| Sem log de auditoria de alterações | rastreabilidade limitada | tabela de eventos administrativos |
| Sem política de senha/2FA | depende do administrador | reforçar checklist operacional |
| CPF armazenado em claro | dados sensíveis | avaliar criptografia/mascaramento conforme policy |

## Checklist de produção

- [ ] `FLASK_CONFIG=production` definido
- [ ] `SECRET_KEY` gerada com `secrets.token_urlsafe(32)`
- [ ] HTTPS obrigatório
- [ ] `wsgi:app` servido por Gunicorn/uWSGI
- [ ] `flask db upgrade` executado no deploy
- [ ] Admin criado com senha forte
- [ ] `seed-demo` **não** executado em produção
- [ ] Uploads com permissão e backup
- [ ] Cabeçalhos de segurança no proxy
- [ ] Monitoramento de 500 e login
- [ ] Backup do SQLite testado

## Resposta a incidentes

1. Para a aplicação se houver suspeita de vazamento de sessão.
2. Rotacione `SECRET_KEY`; isso invalida sessões ativas.
3. Faça backup do banco antes de qualquer limpeza.
4. Revise logs de 500 e acessos ao `/auth/login`.
5. Verifique administradores existentes:

```bash
flask --app run.py shell
```

```python
db.session.scalars(db.select(Administrador)).all()
```

6. Altere a senha do administrador com `definir_senha()` seguido de `db.session.commit()`.

## Leitura complementar

- [Configuração](CONFIGURACAO.md)
- [Testes](TESTES.md)
- [Manutenção](MANUTENCAO.md)
