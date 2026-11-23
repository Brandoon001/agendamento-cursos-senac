# Interface

## Objetivo

Documentar templates, componentes, CSS, JavaScript, CDNs e acessibilidade da interface modernizada. Veja também [Painel administrativo](PAINEL_ADMINISTRATIVO.md), [Formulários](FORMULARIOS.md) e [Segurança](SEGURANCA.md).

## Stack visual

A base é **Tabler CSS 1.7.5**, com Bootstrap 5.3.9 apenas como bundle JavaScript para collapse/dropdowns e Bootstrap Icons 1.13.2.

| Recurso | Versão | Onde é carregado |
| --- | --- | --- |
| Tabler CSS | `1.7.5` | `app/templates/base.html` e `admin_base.html` |
| Bootstrap Icons | `1.13.2` | ambos os layouts |
| Bootstrap JS bundle | `5.3.9` | ambos os layouts |
| SweetAlert2 | `11.26.25` | ambos os layouts |
| Chart.js | `4.6.1` | somente `admin/dashboard.html` |

Não há CSS do Bootstrap carregado separadamente e não há jQuery/DataTables. Filtros são server-side via query string.

Todas as dependências vêm de `cdn.jsdelivr.net` com versão fixada. Para alterar, edite os dois layouts e o bloco `scripts` do dashboard.

## Layouts

### `app/templates/base.html`

Layout público com:

- `<html lang="pt-BR">`;
- `skip-link` para `#conteudo-principal`;
- `components/navbar.html`;
- `components/flash_messages.html`;
- bloco `content`;
- footer;
- scripts globais e bloco `scripts`.

Usado por `main/`, `catalogo/`, `inscricoes/` e `auth/login.html`.

### `app/templates/admin_base.html`

Layout administrativo com:

- `components/admin_shell.html`;
- flash messages em container próprio;
- `main.page-body`;
- footer;
- mesmos scripts globais.

Usado por todas as telas em `admin/`.

## Árvore de templates

```text
app/templates/
├── base.html
├── admin_base.html
├── components/
│   ├── admin_shell.html
│   ├── curso_card.html
│   ├── flash_messages.html
│   ├── navbar.html
│   └── ui.html
├── main/index.html
├── catalogo/
│   ├── lista_cursos.html
│   └── detalhe_curso.html
├── inscricoes/
│   ├── pre_inscricao.html
│   └── confirmacao.html
├── auth/login.html
├── admin/
│   ├── dashboard.html
│   ├── inscricoes.html
│   └── cursos/
│       ├── lista.html
│       ├── formulario.html
│       ├── turmas.html
│       └── turma_formulario.html
└── errors/
    ├── _layout.html
    ├── 400.html
    ├── 403.html
    ├── 404.html
    └── 500.html
```

## Componentes

### `components/ui.html`

| Macro | Parâmetros | Uso |
| --- | --- | --- |
| `breadcrumb(itens)` | lista de `{label, url}` | navegação estrutural |
| `field(campo, span, help, atributos)` | campo WTForms | input com rótulo, erro e ARIA |
| `checkbox_field(campo, span)` | campo booleano | checkbox com erro |
| `status_badge(status, rotulo)` | valor e texto | badge colorido |
| `stat_card(valor, rotulo, href, icone)` | indicador | card de métrica; opcionalmente link |
| `empty_state(titulo, mensagem, icone)` | textos | estado vazio com `caller()` |

`stat_card` usa whitespace control (`{%- ... -%}`) para não gerar quebras de linha excessivas ao iterar sobre status. Isso é essencial em `admin/dashboard.html` e `admin/inscricoes.html`.

### `components/navbar.html`

Navegação pública com marca, link “Cursos gratuitos” e link externo único para `config.PORTAL_CURSOS_URL`. O link externo usa `target="_blank"` e `rel="noopener noreferrer"`.

Marca `active` e `aria-current="page"` para os endpoints de catálogo/inscrição.

### `components/admin_shell.html`

Topbar + sidebar do painel. Calcula `endpoint_atual` e marca `rota_cursos`/`rota_inscricoes` para destacar a navegação.

Logout é um POST com token CSRF explícito.

### `components/flash_messages.html`

Renderiza `get_flashed_messages(with_categories=true)` em `div.flash-stack` com `aria-live="polite"`. Mapeia categorias:

| Categoria | Classe Bootstrap |
| --- | --- |
| `success`, `sucesso` | `alert-success` |
| `error`, `danger` | `alert-danger` |
| `warning` | `alert-warning` |
| `info` ou desconhecida | `alert-info` |

Ícones Bootstrap por categoria. Botão de fechar usa `data-dismiss`.

### `components/curso_card.html`

Macro `curso_card(curso)` com imagem ou placeholder, badge `Gratuito · <cidade>`, descrição truncada, carga horária, vagas e ações. Botão de pré-inscrição aparece apenas quando `aceita_pre_inscricao and possui_vagas`.

## CSS

Arquivo: `app/static/css/style.css` (1127 linhas), organizado em seções identificadas por comentários.

### Tokens

Variáveis em `:root`, com o azul institucional do SENAC e amarelo como destaque:

| Variável | Valor |
| --- | --- |
| `--senac-blue` | `#004a8d` |
| `--senac-blue-dark` | `#003b71` |
| `--senac-blue-soft` | `#e6f0f8` |
| `--senac-blue-rgb` | `0, 74, 141` |
| `--senac-accent` | `#ffb822` |
| `--senac-accent-light` | `#ffe08a` |
| `--senac-accent-dark` | `#f19300` |
| `--senac-accent-ink` | `#8a5000` |
| `--senac-secondary` | `#3182a7` |
| `--senac-text` | `#333539` |
| `--senac-muted` | `#686a6c` |
| `--senac-border` | `#e4e7eb` |
| `--senac-surface` | `#f8f8f8` |
| `--senac-success` / `--senac-success-soft` | `#15734e` / `#e6f4ea` |
| `--senac-danger` / `--senac-danger-soft` | `#b42318` / `#fdecec` |
| `--senac-warning` / `--senac-warning-soft` | `#8a5000` / `#fff4e0` |
| `--senac-info` / `--senac-info-soft` | `#003b71` / `#e6f0f8` |
| `--senac-contact` / `--senac-contact-soft` | `#1d5f7d` / `#e4f1f6` |
| `--senac-radius` | `14px` |
| `--senac-shadow` | sombra suave |

As variáveis também sobrescrevem `--bs-primary` e `--tblr-primary` para manter a identidade sem duplicar CSS. O amarelo é usado em CTA, eyebrow, ícones, borda do rodapé, protocolo e badges de atenção; o azul participa de header, hero, links, botões primários e tabelas.

### Blocos visuais

- `public-header`, `public-main`, `site-footer`;
- `senac-hero`, `section-block`, `section-heading`;
- `course-card`, `course-meta`, `course-detail`;
- `filter-panel`, `filter-grid`, `filter-actions`;
- `admin-topbar`, `admin-sidebar`, `admin-page-header`;
- `stat-card`, `chart-box`, `table-panel`;
- `status-badge`, `empty-state`, `comprovante`;
- `field`, `form-grid`, `form-actions`;
- `flash-stack`, `flash`;
- `error-code`.

### Cores de status

| Classe | Uso |
| --- | --- |
| `status-badge--gratuito`, `--ativo`, `--ativa`, `--finalizada` | verde |
| `status-badge--inativo`, `--inativa`, `--encerrado`, `--cancelada` | vermelho |
| `status-badge--recebida`, `--warning` | âmbar |
| `status-badge--em_analise` | azul (`--senac-info`) |
| `status-badge--contatada` | azul secundário (`--senac-contact`) |

### Responsividade

| Breakpoint | Ajuste |
| --- | --- |
| `max-width: 991px` | sidebar vira bloco inferior; filtros em colunas automáticas |
| `max-width: 767px` | detalhe do curso e formulários em uma coluna; botões de filtro esticados |
| `max-width: 520px` | ações ocupam largura total; hero com menos padding |

`@media (prefers-reduced-motion: reduce)` desativa animações e transições.

## JavaScript

Arquivo: `app/static/js/main.js`.

Executa em `DOMContentLoaded`:

1. botões `data-dismiss` removem o flash pai;
2. flashes `.flash--success` são removidos após 7 s;
3. formulários com `data-confirm` abrem confirmação SweetAlert2, com fallback para `window.confirm`;
4. `input[data-mask='cpf']` aplica máscara `000.000.000-00`;
5. `input[data-mask='telefone']` aplica máscara `(00) 0000-0000` ou `(00) 00000-0000`.

A confirmação usa `form.dataset.confirmed` e `requestSubmit()` para evitar loop. Não há validação de negócio no JavaScript.

## Acessibilidade

- `skip-link` nos dois layouts.
- `aria-current` na navegação ativa.
- `aria-invalid` e `aria-describedby` em campos com erro.
- `aria-label` em botões e selects sem texto visível.
- `role="status"` nos flashes.
- `role="img"` e `aria-label` no canvas do gráfico.
- `:focus-visible` com outline visível.
- Contraste alto para badges e botões primários.
- Respeito a `prefers-reduced-motion`.

## Correções de regressão preservadas

- Loops de status usam whitespace control em `admin/dashboard.html` e `admin/inscricoes.html`.
- `stat_card` usa `{%- ... -%}` em `components/ui.html`.
- Gráfico confinado por `.chart-box`.
- `contar_por_status()` inclui status com zero, evitando cards ausentes.
- Nenhuma dependência duplicada de Bootstrap CSS.

## Como alterar a identidade visual

1. Ajuste os tokens em `:root`.
2. Atualize `--bs-primary-rgb` se a cor primária mudar.
3. Revise `.public-header`, `.senac-hero`, `.site-footer` e `.status-badge`.
4. Atualize `<meta name="theme-color">` nos layouts.
5. Replique a cor primária em `static/js/main.js` (SweetAlert2), `admin/dashboard.html` (Chart.js) e `services/exportacao_service.py` (XLSX).
6. Atualize as asserções de cor em `tests/test_admin_ui.py`.
7. Execute testes e smoke de CDNs/HTML.

## Leitura complementar

- [Formulários](FORMULARIOS.md)
- [Painel administrativo](PAINEL_ADMINISTRATIVO.md)
- [Testes](TESTES.md)
