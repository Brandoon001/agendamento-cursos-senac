# Modelos

## Objetivo

Referência detalhada das classes SQLAlchemy do Agenda-Senac. Para estrutura física, índices e migrações, veja [Banco de dados](BANCO_DE_DADOS.md). Para comportamento, veja [Serviços](SERVICOS.md) e [Fluxos de negócio](FLUXOS_DE_NEGOCIO.md).

## Mapa de modelos

| Arquivo | Classe | Tabela |
| --- | --- | --- |
| `app/models/administrador.py` | `Administrador` | `administradores` |
| `app/models/curso.py` | `Curso` | `cursos` |
| `app/models/turma.py` | `Turma` | `turmas` |
| `app/models/inscricao.py` | `Inscricao` | `inscricoes` |
| `app/models/base.py` | `TimestampMixin`, `utcnow()` | — |
| `app/models/enums.py` | `TipoCurso`, `StatusInscricao`, `STATUS_LABELS` | — |

`app/models/__init__.py` reexporta todas as classes e é usado por `create_app()` para registrar os modelos antes das migrações/consultas.

## `TimestampMixin` e `utcnow()`

Implementação em `app/models/base.py:10-28`.

| Coluna | Configuração |
| --- | --- |
| `criado_em` | `DateTime(timezone=True)`, `default=utcnow`, `nullable=False` |
| `atualizado_em` | `DateTime(timezone=True)`, `default=utcnow`, `onupdate=utcnow`, `nullable=False` |

`utcnow()` retorna `datetime.now(timezone.utc)`. Não há `server_default`; objs criados por SQL puro devem preencher as colunas manualmente.

Todas as entidades herdam esse mixin.

## `TipoCurso`

Arquivo: `app/models/enums.py:8-11`.

```python
class TipoCurso(str, Enum):
    GRATUITO = "gratuito"
```

Embora a constraint legada aceite `pago`, o enum atual contém apenas `gratuito`. `CursoService` força esse valor em toda criação/edição.

## `StatusInscricao`

Arquivo: `app/models/enums.py:14-34`.

| Membro | Valor gravado | Rótulo em `STATUS_LABELS` |
| --- | --- | --- |
| `RECEBIDA` | `recebida` | Recebida |
| `EM_ANALISE` | `em_analise` | Em análise |
| `CONTATADA` | `contatada` | Contatada |
| `FINALIZADA` | `finalizada` | Finalizada |
| `CANCELADA` | `cancelada` | Cancelada |

Fluxo esperado: `recebida → em_analise → contatada → finalizada`. `cancelada` pode ocorrer a qualquer momento. Não há constraint de transição no banco; `InscricaoService.alterar_status()` aceita qualquer membro do enum.

## `Administrador`

Arquivo: `app/models/administrador.py:12-52`.

| Campo | Tipo | Observações |
| --- | --- | --- |
| `id` | `Integer` | chave primária |
| `nome` | `String(120)` | obrigatório |
| `email` | `String(255)` | obrigatório, único, indexado |
| `senha_hash` | `String(255)` | hash Werkzeug, nunca senha pura |
| `ativo` | `Boolean` | padrão `True` |
| `criado_em`, `atualizado_em` | herança | — |

Relação:

- `inscricoes` → `Inscricao`, `back_populates="administrador"`, `foreign_keys="Inscricao.administrador_id"`, `passive_deletes=True`. Representa inscrições cuja situação foi alterada por este administrador.

Flask-Login exige `get_id()`, fornecido por `UserMixin`, que retorna `str(self.id)`. A classe sobrescreve `is_active` (`app/models/administrador.py:42-49`) para integrar a coluna `ativo`. Objetos novos ainda não flushed são considerados ativos.

Métodos de senha em `app/models/administrador.py:34-40`:

```python
admin.definir_senha("senha")
admin.verificar_senha("senha")  # True
```

`definir_senha()` usa `generate_password_hash`; `verificar_senha()` usa `check_password_hash`.

A regra de unicidade do administrador não está no banco: ela é aplicada pelo comando `criar-admin` em `app/cli.py:83-99`.

## `Curso`

Arquivo: `app/models/curso.py:14-158`.

### Campos

| Campo | Tipo | Observações |
| --- | --- | --- |
| `id` | `Integer` | PK |
| `titulo` | `String(150)` | obrigatório |
| `slug` | `String(180)` | único, opcional, indexado; gerado por `gerar_slug()` |
| `cidade` | `String(100)` | padrão `Sobral`, indexado |
| `descricao` | `Text` | obrigatório no serviço; padrão `""` no banco |
| `tipo` | `Enum(TipoCurso)` | sempre `gratuito` na aplicação, indexado |
| `link_externo` | `String(500)` | legado; sempre `None` na aplicação |
| `valor` | `Numeric(10, 2)` | legado; sempre `None` na aplicação |
| `carga_horaria` | `Integer` | opcional, `> 0` |
| `data_inicio`, `data_fim` | `Date` | opcionais, `data_fim >= data_inicio` |
| `vagas` | `Integer` | opcional, `>= 0`; referência informativa quando não há turmas |
| `imagem_url` | `String(500)` | opcional |
| `ativo` | `Boolean` | padrão `True`, indexado |

### Relações

```python
inscricoes = db.relationship(
    "Inscricao",
    back_populates="curso",
    passive_deletes=True,
)
turmas = db.relationship(
    "Turma",
    back_populates="curso",
    cascade="all, delete-orphan",
    passive_deletes=True,
    order_by="Turma.nome",
)
```

`CursoService.excluir_curso()` bloqueia a exclusão quando `curso.inscricoes` não está vazio. Para arquivar, use `ativo = False`.

### Propriedades

| Propriedade | Retorno | Regra |
| --- | --- | --- |
| `situacao` | `str` | `"ativo"` ou `"inativo"` |
| `aceita_pre_inscricao` | `bool` | `ativo is not False`; objetos novos sem flush são considerados ativos |
| `turmas_ativas` | `list[Turma]` | turmas com `ativo is not False`, na ordem de `turmas` |
| `vagas_ocupadas` | `int` | inscrições com `status != CANCELADA` |
| `vagas_disponiveis` | `int \| None` | soma das vagas das turmas ativas; sem turmas, usa `Curso.vagas`; `None` = ilimitado |
| `possui_vagas` | `bool` | curso inativo → `False`; sem turmas → `vagas is None or vagas_disponiveis > 0`; com turmas → `any(turma.disponivel ...)` |

`vagas_disponiveis` retorna `None` se qualquer turma ativa tiver `vagas is None`.

### Representação

```python
repr(curso)  # <Curso 'Arquitetura de Software' (Sobral)>
```

## `Turma`

Arquivo: `app/models/turma.py:10-105`.

| Campo | Tipo | Observações |
| --- | --- | --- |
| `id` | `Integer` | PK |
| `curso_id` | `Integer` | FK `cursos.id`, `ON DELETE CASCADE`, obrigatório, indexado |
| `nome` | `String(100)` | obrigatório |
| `dias_semana` | `String(120)` | texto livre, por exemplo `Seg, Qua, Sex` |
| `hora_inicio`, `hora_fim` | `Time` | opcionais, `hora_fim > hora_inicio` |
| `data_inicio`, `data_fim` | `Date` | opcionais, `data_fim >= data_inicio` |
| `vagas` | `Integer` | opcional, `>= 0`; `None` = ilimitado |
| `ativo` | `Boolean` | padrão `True`, indexado |

Relações:

- `curso` → `back_populates="turmas"`.
- `inscricoes` → `back_populates="turma"`, `passive_deletes=True`.

`Turma` **não** usa `cascade="all, delete-orphan"` nas inscrições. A exclusão é bloqueada no serviço quando há inscrições; a FK usa `ON DELETE SET NULL` para preservar o histórico caso a turma seja removida por outro caminho.

### Propriedades

| Propriedade | Retorno | Regra |
| --- | --- | --- |
| `situacao` | `str` | `"ativa"` ou `"inativa"` |
| `vagas_ocupadas` | `int` | inscrições com `status != CANCELADA` |
| `vagas_disponiveis` | `int \| None` | `None` se ilimitado; senão `max(vagas - ocupadas, 0)` |
| `tem_vagas` | `bool` | `vagas is None or vagas_disponiveis > 0` |
| `disponivel` | `bool` | `ativo is not False`, curso ativo (ou sem curso carregado) e `tem_vagas` |
| `horario_formatado` | `str` | `"08:00 às 12:00"` ou `"Horário a definir"` |

```python
repr(turma)  # <Turma 'Turma Manhã' curso=1>
```

## `Inscricao`

Arquivo: `app/models/inscricao.py:16-109`.

### Campos

| Campo | Tipo | Observações |
| --- | --- | --- |
| `id` | `Integer` | PK; usado no protocolo |
| `curso_id` | `Integer` | FK obrigatória, `RESTRICT`, indexada |
| `administrador_id` | `Integer` | FK opcional, `SET NULL`, indexada |
| `turma_id` | `Integer` | FK opcional, `SET NULL`, indexada |
| `nome_completo` | `String(150)` | obrigatório |
| `cpf` | `String(14)` | único global; gravado como `000.000.000-00` |
| `email` | `String(255)` | opcional, indexado |
| `telefone` | `String(20)` | opcional |
| `data_nascimento` | `Date` | opcional |
| `observacoes` | `Text` | opcional |
| `status` | `Enum(StatusInscricao)` | padrão `RECEBIDA`, indexado |

Relações:

- `curso` → `back_populates="inscricoes"`.
- `turma` → `back_populates="inscricoes"`.
- `administrador` → `back_populates="inscricoes"`, `foreign_keys=[administrador_id]`.

### Propriedades

| Propriedade | Exemplo | Regra |
| --- | --- | --- |
| `protocolo` | `INS-2026-00007` | `INS-{ano}-{id:05d}`; ano vem de `criado_em` ou `date.today()`; sem ID usa `00000` |
| `situacao` | `Em análise` | `STATUS_LABELS[self.status]`, com fallback `"Desconhecida"` |

```python
repr(inscricao)  # <Inscricao 'Maria Silva' curso=1>
```

O CPF é gravado pelo serviço já formatado; o modelo não possui propriedade de formatação. Para normalizar, use `somente_digitos` e `formatar_cpf` de `app/forms/inscricao.py`.

## Invariantes recomendadas

Ao escrever código que manipula modelos diretamente, preserve estas regras:

1. Normalize CPF com `validar_cpf`/`formatar_cpf` antes de persistir.
2. Crie inscrições somente para cursos com `aceita_pre_inscricao == True`.
3. Valide `turma.disponivel` ao informar `turma_id`.
4. Não remova curso ou turma com inscrições; desative-os.
5. Use `StatusInscricao` em vez de strings literais.
6. Atualize `administrador_id` ao alterar status pelo painel.
7. Não grave `imagem_url == ""`; use `None`.
8. Revalide migrações ao alterar `nullable`, índices ou enums.

## Leitura complementar

- [Banco de dados](BANCO_DE_DADOS.md)
- [Serviços](SERVICOS.md)
- [Formulários](FORMULARIOS.md)
