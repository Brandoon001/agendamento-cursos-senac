# Índice da documentação

Esta pasta é a fonte central de documentação do **Agenda-Senac**. Ela descreve o estado atual do projeto: Flask + Jinja2 + SQLAlchemy + SQLite, com painel administrativo, catálogo público e pré-inscrições.

Comece pelo [README.md](../README.md) para visão geral e execução rápida. Depois use este índice para aprofundar cada área.

## Mapa de documentos

| Documento | Para que serve | Leia quando... |
| --- | --- | --- |
| [ARQUITETURA.md](ARQUITETURA.md) | Estrutura em camadas, Application Factory, blueprints e ciclo de requisição | precisar entender como o app é montado |
| [CONFIGURACAO.md](CONFIGURACAO.md) | `.env`, ambientes, variáveis e ajustes de produção | fornecer/instalar/configurar o projeto |
| [BANCO_DE_DADOS.md](BANCO_DE_DADOS.md) | Modelo ER, constraints, índices e migrações | mexer em schema, dados ou Alembic |
| [MODELOS.md](MODELOS.md) | Referência detalhada de `Curso`, `Turma`, `Inscricao`, `Administrador` e enums | escrever regras ou consultas |
| [SERVICOS.md](SERVICOS.md) | Regras de negócio implementadas nos serviços | alterar validações ou persistência |
| [FORMULARIOS.md](FORMULARIOS.md) | WTForms, validadores e mensagens | mexer em formulários ou entrada do usuário |
| [FLUXOS_DE_NEGOCIO.md](FLUXOS_DE_NEGOCIO.md) | Jornadas completas e invariantes | entender o comportamento fim a fim |
| [ROTAS.md](ROTAS.md) | Tabela completa de endpoints, métodos e permissões | adicionar ou depurar rotas |
| [PAINEL_ADMINISTRATIVO.md](PAINEL_ADMINISTRATIVO.md) | Uso operacional do painel e rotinas administrativas | trabalhar no admin ou responder chamados |
| [INTERFACE.md](INTERFACE.md) | Templates, componentes, CSS, JS, CDN e acessibilidade | alterar layout, estilo ou comportamento visual |
| [SEGURANCA.md](SEGURANCA.md) | Autenticação, CSRF, upload, XLSX e pendências | revisar riscos ou preparar produção |
| [TESTES.md](TESTES.md) | Comandos, fixtures, cobertura e lacunas | rodar/escrever testes |
| [CLI.md](CLI.md) | Comandos Flask, seed e shell | criar admin, Popular demo ou inspecionar dados |
| [MANUTENCAO.md](MANUTENCAO.md) | Deploy, backup, troubleshooting e dívida técnica | manter ou diagnosticar o sistema |
| [MODULO_CURSOS.md](MODULO_CURSOS.md) | Documentação original de estudo do módulo de cursos | consultar decisões históricas do domínio de cursos |

## Convenções

- Caminhos de arquivo são relativos à raiz do repositório, salvo indicação contrária.
- Endpoints são escritos no formato do Flask, por exemplo `admin.inscricoes`.
- Diagramas usam Mermaid e podem ser renderizados no GitHub.
- Quando uma regra aparece em mais de um documento, o documento dono da regra é linkado a partir dos demais.
- Os números de linha citados refletem o estado atual do working tree e podem mudar após refatorações; os caminhos dos arquivos são a referência estável.

## Comandos mais usados

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
flask --app run.py db upgrade
flask --app run.py criar-admin
flask --app run.py run --debug
```

## Ordem sugerida de leitura

1. [README.md](../README.md)
2. [ARQUITETURA.md](ARQUITETURA.md)
3. [CONFIGURACAO.md](CONFIGURACAO.md)
4. [BANCO_DE_DADOS.md](BANCO_DE_DADOS.md)
5. [FLUXOS_DE_NEGOCIO.md](FLUXOS_DE_NEGOCIO.md)
6. [ROTAS.md](ROTAS.md) e [PAINEL_ADMINISTRATIVO.md](PAINEL_ADMINISTRATIVO.md)
7. [TESTES.md](TESTES.md) e [MANUTENCAO.md](MANUTENCAO.md)
