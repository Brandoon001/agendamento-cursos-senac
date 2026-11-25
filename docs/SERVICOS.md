# Serviços

## Objetivo

Documentar as classes e funções que concentram as regras de negócio. As rotas devem delegar para aqui; veja [Rotas](ROTAS.md), [Modelos](MODELOS.md) e [Fluxos de negócio](FLUXOS_DE_NEGOCIO.md).

## Mapa de serviços

| Arquivo | Símbolo | Responsabilidade |
| --- | --- | --- |
| `app/services/curso_service.py` | `CursoService` | Cursos, turmas, slug, visibilidade pública |
| `app/services/curso_service.py` | `gerar_slug`, `cidade_padrao`, `curso_esta_visivel` | Funções auxiliares |
| `app/services/inscricao_service.py` | `InscricaoService` | Criação, listagem, contagem e status de inscrições |
| `app/services/autenticacao_service.py` | `AutenticacaoService` | Validação de credenciais |
| `app/services/upload_imagem_service.py` | `UploadImagemService` | Salvamento/remoção de imagens |
| `app/services/exportacao_service.py` | `gerar_planilha_inscricoes` | Geração do XLSX |
| `app/services/__init__.py` | — | Reexportações e documentação do pacote |

Não existe `TurmaService`: operações de turma estão em `CursoService`.

## `CursoService`

Arquivo: `app/services/curso_service.py:55-383`.

### Consultas

| Método | Retorno | Regras |
| --- | --- | --- |
| `listar_cursos_publicos(termo=None, cidade=None)` | `list[Curso]` | `ativo=True`, `tipo=GRATUITO`, `cidade == cidade or cidade_padrao()`; busca `ILIKE` em título/descrição; ordena por título |
| `listar_todos(termo=None, situacao=None)` | `list[Curso]` | Inclui inativos; `situacao` aceita `ativo`/`inativo`; ordena por título |
| `obter_curso(curso_id)` | `Curso \| None` | `db.session.get` |
| `listar_turmas(curso_id, apenas_ativas=False)` | `list[Turma]` | Ordena por `Turma.nome` |
| `listar_turmas_disponiveis(curso_id)` | `list[Turma]` | Filtra `turma.disponivel` entre ativas |
| `obter_turma(turma_id)` | `Turma \| None` | `db.session.get` |

`cidade_padrao()` lê `current_app.config["CIDADE_PADRAO"]` com fallback `"Sobral"`.

### Escrita

| Método | Efeito |
| --- | --- |
| `criar_curso(dados)` | Normaliza dados, gera slug único, persiste |
| `atualizar_curso(curso, dados)` | Reaplica normalização e persiste |
| `definir_situacao(curso, ativo)` | Alterna `Curso.ativo` |
| `excluir_curso(curso)` | Bloqueia se houver inscrições; remove arquivo de imagem no route |
| `criar_turma(curso_id, dados)` | Cria turma vinculada ao curso |
| `atualizar_turma(turma, dados)` | Atualiza campos da turma |
| `definir_situacao_turma(turma, ativo)` | Alterna `Turma.ativo` |
| `excluir_turma(turma)` | Bloqueia se houver inscrições |

### Normalização e validação

`_aplicar_dados_do_curso()`:

- exige `titulo` e `descricao` não vazios;
- cidade padrão quando ausente, no máximo 100 caracteres;
- força `tipo = TipoCurso.GRATUITO`, `link_externo = None`, `valor = None`;
- `carga_horaria > 0`, `vagas >= 0` e `data_fim >= data_inicio`;
- `imagem_url = texto or None`;
- slug informado ou gerado pelo título, sempre passando por `gerar_slug()`;
- `_slug_unico()` acrescenta `-2`, `-3` etc. quando há conflito, ignorando o próprio ID na edição.

`_aplicar_dados_da_turma()`:

- exige `nome`;
- início e fim devem ser informados juntos e `hora_fim > hora_inicio`;
- `data_fim >= data_inicio`;
- `vagas >= 0`;
- `ativo` padrão `True`.

Conversores privados: `_texto`, `_booleano`, `_inteiro`, `_data`, `_hora`. Todos lançam `ValueError` com mensagem amigável.

`_salvar()` faz `commit`, e em qualquer exceção executa `rollback()` e relança `ValueError(mensagem)`.

### `curso_esta_visivel()`

`app/services/curso_service.py:386-393` é o filtro usado por rotas públicas:

```python
curso is not None
and curso.ativo is not False
and curso.tipo is TipoCurso.GRATUITO
and curso.cidade == cidade_padrao()
```

Rota invisível retorna `404` em `catalogo.detalhe` e `inscricoes.pre_inscricao`.

## `InscricaoService`

Arquivo: `app/services/inscricao_service.py:17-157`.

### `criar_pre_inscricao(curso_id, dados, turma_id=None)`

Validações, nesta ordem:

1. curso existe e `curso.aceita_pre_inscricao` é verdadeiro;
2. se `turma_id` informado: turma existe, pertence ao curso, está ativa e `turma.disponivel`;
3. CPF informado e válido pelos dígitos verificadores;
4. CPF não existe em nenhuma inscrição do sistema;
5. persistência com status `RECEBIDA`.

O CPF é armazenado com máscara por `formatar_cpf()`. `IntegrityError` no commit gera rollback e `ValueError("Já existe uma pré-inscrição com este CPF.")`.

Importante: o serviço **não** verifica diretamente `Curso.vagas` nem `Curso.possui_vagas`. Quando não há turma, a inscrição pode ser criada mesmo com `vagas=0`; a interface pública usa `possui_vagas` para esconder o botão. Veja [Fluxos de negócio](FLUXOS_DE_NEGOCIO.md).

### `listar_inscricoes(curso_id=None, status=None, termo=None)`

- usa `joinedload` para `curso` e `turma`;
- filtra curso, status e termo;
- status inválido retorna `[]`;
- o termo usa `ILIKE` em nome, CPF e e-mail, com `%` e `_` escapados;
- ordena por `criado_em desc`, depois `id desc`.

### `alterar_status(inscricao_id, status, administrador_id)`

- converte string para `StatusInscricao` com `_converter_status()`;
- rejeita status inválido com `ValueError`;
- grava `status` e `administrador_id`;
- faz rollback em qualquer exceção no commit.

### `contar_por_status()`

Retorna `dict[StatusInscricao, int]` com **todas** as situações presentes, incluindo as que têm zero. Isso evita que cards/gráficos do painel desapareçam quando não há registros em um status.

## `AutenticacaoService`

Arquivo: `app/services/autenticacao_service.py:9-27`.

`autenticar(email, senha)`:

1. normaliza e-mail com `strip().lower()`;
2. rejeita e-mail ou senha vazios;
3. consulta `Administrador` por e-mail em minúsculas;
4. exige `administrador.is_active`;
5. valida hash com `verificar_senha`.

Retorna `Administrador | None`. Não há bloqueio por tentativas nem logging de falhas de login; veja [Segurança](SEGURANCA.md).

## `UploadImagemService`

Arquivo: `app/services/upload_imagem_service.py:20-83`.

### `salvar(arquivo)`

- valida extensão original contra `UPLOAD_EXTENSOES_IMAGEM`;
- detecta assinatura real do arquivo: PNG, JPG (`\xff\xd8\xff`), GIF87a/GIF89a ou WebP (`RIFF....WEBP`);
- rejeita arquivo vazio, acima de `MAX_CONTENT_LENGTH` ou sem assinatura conhecida;
- gera nome UUID (`<hex>.<ext>`);
- salva em `UPLOAD_FOLDER`;
- retorna `UPLOAD_URL_PREFIX + nome`.

Um arquivo `.jpeg` é aceito pela extensão, mas salvo com extensão `.jpg` porque a assinatura detectada é JPG.

### `remover(imagem_url)`

Remove apenas arquivos cuja URL comece com `UPLOAD_URL_PREFIX` e cujo nome não contenha `/`, `\` ou `..`. URLs externas são ignoradas. A remoção é chamada pelo route quando a imagem é substituída ou o curso é excluído.

## `gerar_planilha_inscricoes(inscricoes)`

Arquivo: `app/services/exportacao_service.py:32-78`.

- cria aba `Inscrições`;
- cabeçalho fixo com 11 colunas;
- usa `protocolo`, `situacao`, curso/turma e datas formatadas;
- aplica larguras, `freeze_panes = "A2"` e auto-filtro;
- protege contra injeção de fórmulas: strings que começam com `=`, `+`, `-` ou `@` têm `data_type = "s"`;
- retorna `bytes` do XLSX.

O filtro aplicado ao download é o mesmo da tela, lido da query string em `app/blueprints/admin/routes.py:420-426`.

## Convenções e tratamento de erros

- Serviços recebem `Mapping[str, object]`, não `FlaskForm`.
- Erros de regra de negócio são `ValueError` com mensagem para `flash()`.
- `commit`/`rollback` ficam nos serviços; rotas apenas exibem mensagens.
- Nenhum serviço usa cache, fila ou transação distribuída.
- A checagem de vaga na criação é feita antes do `commit`; em alta concorrência pode haver corrida pela última vaga. Veja [Segurança](SEGURANCA.md).

## Leitura complementar

- [Modelos](MODELOS.md)
- [Formulários](FORMULARIOS.md)
- [Segurança](SEGURANCA.md)
