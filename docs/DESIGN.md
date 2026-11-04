# Definições de design

Valem para o projeto inteiro, antes de criar ou alterar qualquer tela, template, componente ou o boletim.
Definidas pelo usuário em 2026-11-04. Não mudam a engenharia (stack, modelo de dados, testes).

## Contexto

App de gestão interno da yeshiva Or Yossef, não um site de marketing. Não existe hero nem seção de apresentação: a primeira coisa na tela é o que o usuário precisa fazer.
Usuários: direção (mais no computador), rabino da turma e rabinos de matéria (muitas vezes no celular, com pressa). A familiaridade com tecnologia é média. **O caso que define o design é o rabino no celular com pressa.**

## Identidade visual

Tokens (em `app/static/src/app.css`, no `@theme` do Tailwind 4; nunca hex avulso nas classes):

| Token | Cor | Uso |
|---|---|---|
| primary | #005A8E | Azul do logo: ação principal, navegação ativa, cabeçalho |
| primary-dark | #00466F | Hover, títulos |
| primary-light | #E6F0F6 | Linha selecionada, aba ativa |
| gray | #6E6E6E | Texto secundário, rótulos |
| text | #1F2933 | Texto principal |
| border | #DDE3E8 | |
| surface | #F7F9FA | Fundo de áreas |
| background | #FFFFFF | |
| success | #2E7D4F | Só para status |
| warning | #B7791F | Só para status |
| danger | #B42318 | Só para status |

- O azul é para o que importa. A maior parte da tela é branca, com texto escuro e cinza.
- Fontes: Montserrat só em títulos. IBM Plex Sans em todo o resto. IBM Plex Sans Hebrew para texto em hebraico, com `lang="he"` e `dir="rtl"` no elemento.
- No máximo 5 tamanhos de fonte no app. Corpo com pelo menos 16px, nada abaixo de 14px.
- Números em tabelas com `tabular-nums`, sempre alinhados do mesmo jeito.
- Cantos de 4 a 6px. Sombras quase imperceptíveis, só no que flutua (menu aberto, modal).
- O padrão de "Y" do logo só aparece na tela de login e no cabeçalho do boletim, discreto.

## Princípios de UX

1. Toda tela mostra primeiro o que falta fazer, com atalho direto para resolver.
2. Uma ação principal (primary) por tela ou seção. Ações destrutivas em danger, separadas e sempre com confirmação.
3. Nada importante escondido: sem ações só em menu de três pontinhos, sem ícone sem rótulo, sem nada que só apareça no hover.
4. Retorno sempre visível: indicador de "Salvando / Salvo / Não foi possível salvar", e "Desfazer" quando der.
5. Toda tela tem os estados vazio, carregando, erro e cheio. O vazio convida a agir ("Nenhum shiur neste ano. Criar shiur.").
6. Alvos de toque com pelo menos 44px de altura.
7. Grade de notas: nome do aluno fixo à esquerda, cabeçalho fixo, Enter desce, Tab vai para a direita, setas navegam, aceita vírgula ou ponto, célula inválida marcada sem bloquear as outras. No celular, vira uma lista de alunos com o campo da nota, uma prova por vez.
8. Formulários: rótulo sempre visível acima do campo (nunca só placeholder), validação ao sair do campo.
9. Nada se mexe sozinho. Transições de 150 a 200ms só para mostrar o que mudou. Respeitar `prefers-reduced-motion`.
10. Foco de teclado sempre visível, contraste de texto de pelo menos 4.5:1, status nunca só por cor, HTML semântico.

## Proibido (cara de app gerado por AI)

Gradientes; emojis; tudo em cartões idênticos com raio grande e a mesma sombra; rótulos em CAIXA ALTA espaçada acima dos títulos; uma palavra do título em outra cor ou itálico; números decorativos (01, 02, 03) em conteúdo que não é sequência; textos juntados com ponto do meio só por estilo; seta "→" em botões; fonte monoespaçada para dados; cartões de "número grande com rótulo pequeno" só para enfeitar; animação de entrada em cada seção; hover em todos os cartões; ícone decorativo ao lado de cada título; roxo, verde-limão ou fundo creme.

## Textos da interface (português)

- Frase normal, não Título Com Maiúsculas ("Criar shiur").
- Botões dizem o que acontece ("Salvar notas", "Marcar shiur como pronto"), nunca só "Enviar" ou "OK".
- A mesma ação tem o mesmo nome no fluxo inteiro ("Liberar boletins" gera "Boletins liberados").
- Vocabulário da yeshiva (shiur, rabino, prova, trimestre, boletim), nunca termos técnicos.
- Erros diretos, dizendo como resolver, sem pedir desculpas ("A nota precisa estar entre 0 e 10.").
- Confirmações dizem o que vai acontecer ("Remover Moshe Cohen do Shiur Bet? As notas dele neste shiur continuam guardadas.").

## Componentes

Todo elemento repetido vira macro Jinja em `app/templates/components/` e é reutilizado. Mínimo: button (primary, secondary, danger, ghost), input, select, textarea, field (rótulo + campo + erro + ajuda), table, grade_cell, badge de status, alert, toast, modal de confirmação, empty_state, tabs, page_header, pending_item, file_upload (com câmera no celular), save_indicator.

## Processo para cada tela

1. Planejar: o trabalho principal da tela em uma frase, quem usa e em que aparelho, wireframe em ASCII para computador e celular, ação principal e secundárias, estados, componentes usados.
2. Revisar o plano contra estes princípios e a lista do proibido. Se algo parece a escolha padrão que você faria para qualquer app, troque e diga por quê. Mostrar o plano e esperar aprovação.
3. Construir só com tokens e componentes.
4. Tirar prints em 375px, 768px e 1280px e analisar. Antes de entregar, remover um enfeite.
5. Conferir: ação principal óbvia em 3 segundos; funciona nas três larguras sem rolagem horizontal da página; todos os estados existem; toda ação dá retorno; navegável por teclado; contraste ok; alvos de 44px; só tokens e componentes; nada da lista do proibido; hebraico com a fonte e a direção certas.

## Boletim em PDF (A4)

Logo em vetor no topo com o padrão de "Y" discreto. Azul só no cabeçalho e nos títulos das seções, o resto em preto e cinza, legível em impressora preto e branco. Uma página por aluno sempre que possível. Tabela das matérias limpa, com o rabino de cada matéria e as provas. Frequência e comentários em seções claras, com espaço para assinatura.
