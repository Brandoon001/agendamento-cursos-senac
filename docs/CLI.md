# CLI

## Objetivo

Documentar comandos Flask disponíveis, parâmetros, efeitos e cuidados. Veja também [Configuração](CONFIGURACAO.md), [Banco de dados](BANCO_DE_DADOS.md) e [Testes](TESTES.md).

## Registro

`app/cli.py` define `criar_admin` e `seed_demo`. `registrar_comandos(app)` é chamado por `create_app()`.

O grupo `db` vem do Flask-Migrate e é registrado pela extensão `migrate`.

Listar comandos:

```bash
flask --app run.py --help
flask --app run.py db --help
```

## `criar-admin`

```bash
flask --app run.py criar-admin
```

Parâmetros interativos:

| Parâmetro | Descrição |
| --- | --- |
| `--nome` | nome do administrador |
| `--email` | e-mail de login |
| `--senha` | senha com confirmação (`@click.password_option`) |

Também pode ser não interativo:

```bash
flask --app run.py criar-admin \
  --nome "Administrador" \
  --email "admin@senac.br" \
  --senha "senha-forte-aqui"
```

Regras:

- recusa criação se **qualquer** administrador já existir;
- converte e-mail para minúsculas;
- gera hash com `Administrador.definir_senha()`;
- não há constraint no banco impedindo um segundo administrador inserido por SQL;
- a senha não é exibida.

## `seed-demo`

```bash
flask --app run.py seed-demo
```

Ou com senha explícita:

```bash
flask --app run.py seed-demo --senha "senha-local"
```

Padrões:

| Item | Valor |
| --- | --- |
| Administrador criado se não houver | `admin@senac.br` |
| Senha padrão | `senac123` |
| Cursos | Informática Básica, Comunicação e Expressão, Primeiros Socorros |
| Cidade | `Sobral` |
| Datas | fixas em novembro/dezembro de 2026 |

Comportamento:

- cria administrador apenas se não existir nenhum;
- ignora cursos cujo título já existe;
- cria as turmas definidas em `CURSOS_DEMO`;
- imprime quantidade de cursos criados;
- é adequado para demonstração local, **nunca para produção**.

As datas fixas ficarão obsoletas com o tempo. Para uma demo nova, ajuste `CURSOS_DEMO` em `app/cli.py`.

## Comandos de banco

```bash
flask --app run.py db upgrade
flask --app run.py db downgrade <revisao>
flask --app run.py db migrate -m "descrição"
flask --app run.py db current
flask --app run.py db history
flask --app run.py db heads
```

A cadeia atual termina em `a2b3c4d5e6f7`. Detalhes em [Banco de dados](BANCO_DE_DADOS.md).

## `flask shell`

O shell já recebe objetos do contexto da aplicação (`app/__init__.py:70-81`):

- `db`
- `Administrador`
- `Curso`
- `Turma`
- `Inscricao`

Exemplo:

```bash
flask --app run.py shell
```

```python
db.session.scalars(db.select(Curso)).all()
curso = db.session.get(Curso, 1)
curso.ativo = False
db.session.commit()
```

## Ambientes nos comandos

Por padrão, `run.py` usa `development`. Para forçar outro ambiente:

```bash
FLASK_CONFIG=testing flask --app run.py db upgrade
FLASK_CONFIG=production flask --app run.py db upgrade
```

Em produção, prefira definir `FLASK_CONFIG` no ambiente do servidor e apontar o WSGI para `wsgi:app`.

## Boas práticas

- Sempre faça backup antes de `db upgrade` em produção.
- Não execute `seed-demo` em produção.
- Não crie segundo administrador.
- Prefira `criar-admin` a inserir registros diretamente no banco.
- Revise migrações geradas antes de commitar.
- Documente novos comandos aqui.

## Leitura complementar

- [Configuração](CONFIGURACAO.md)
- [Banco de dados](BANCO_DE_DADOS.md)
- [Manutenção](MANUTENCAO.md)
