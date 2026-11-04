# Componentes (macros Jinja)

Toda tela usa estes componentes. Não criar estilos avulsos (CLAUDE.md).
A galeria com todos eles fica em `/prototipo/componentes`.

## `ui.html`

| Macro | Uso |
|---|---|
| `icon(name, class="size-5")` | Ícone Lucide de `templates/icons/` |
| `button(label, variant, type, href, icon_name, size, full, attrs)` | `variant`: primary, secondary, danger, ghost. `size`: md (44px, padrão), sm (36px, só em tabela no computador). Com `href` vira link. `attrs` é um dict de atributos extras |
| `status(kind, label)` | Selo. `kind`: success, warning, danger, neutral, primary. Sempre ícone + texto |
| `alert(kind, message, title=None)` | Aviso em bloco. `kind`: success, warning, danger, info |
| `card(title, subtitle, padded=True)` | Cartão. Conteúdo no `{% call %}` |
| `page_header(title, subtitle, back_href, back_label)` | Título da página. Ações no `{% call %}` |
| `empty_state(message, icon_name)` | Lista vazia. Ação opcional no `{% call %}` |

## `forms.html`

| Macro | Uso |
|---|---|
| `text_input(name, label, value, type, hint, error, required, placeholder, attrs)` | Campo de texto |
| `select(name, label, options, selected, ...)` | `options`: lista de `(valor, rótulo)` |
| `textarea(name, label, value, rows, maxlength, ...)` | Texto longo |
| `wtf_field(field, hint, attrs)` | Campo de um formulário Flask-WTF, com o mesmo visual e o erro do validador |
| `csrf_field()` | Token CSRF para formulários feitos à mão |

Rótulo sempre visível. Dica e erro embaixo do campo, ligados por `aria-describedby`.

## `table.html`

`data_table(columns, caption, sticky_first)`: as linhas vêm no `{% call %}` como `<tr><td>` simples.
Coluna é um texto ou `(texto, "right")`. No celular, tabela larga rola dentro do cartão;
quando a tabela é a parte principal da tela, mostrar cartões no celular (`md:hidden`) e a
tabela no computador (`hidden md:block`), como em `prototype/home_admin.html`.

## `dialog.html`

`confirm_dialog(id, title, message, confirm_label, action, method, danger)`: confirmação de ação
destrutiva. Abrir com qualquer botão que tenha `attrs={"data-open-dialog": id}`.

## Retorno ao usuário

- Avisos rápidos: `window.dispatchEvent(new CustomEvent("notify", {detail: {kind, message}}))`
  ou, do servidor no HTMX, o cabeçalho `HX-Trigger: {"notify": {"kind": "success", "message": "Salvo"}}`.
  Erros ficam até a pessoa fechar.
- Erro de rede ou do servidor em qualquer requisição HTMX já vira aviso (`static/js/app.js`).
- Mensagens do Flask (`flash(msg, "success")`) aparecem no topo da página.

## Grades de lançamento

`static/js/grade-grid.js` (`x-data="gradeGrid({saveUrl})"`): Enter e setas descem e sobem,
vírgula ou ponto, A/D, validação do máximo, salvamento por nota com estado em `data-state`
(`saving`, `saved`, `error`). Ver `prototype/grades.html`.

## Regras

- Cores e fontes só pelos tokens (`static/src/app.css`). As cores padrão do Tailwind estão desligadas.
- Botões e campos com pelo menos 44px de altura.
- Números em tabelas com `tabular-nums`, alinhados à direita.
- Texto em hebraico com `lang="he" dir="rtl"`.
- Toda tela conferida no celular (390px) e no computador antes de concluir.
