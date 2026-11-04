# Plano do projeto: Sistema de notas de Kodesh da Yeshiva

Documento de referência para desenvolvimento com Claude Code.
Cada fase é pensada para uma ou poucas sessões. Marque os checkboxes conforme avança.

---

## 1. Objetivo

App web para gerenciar as notas das matérias de kodesh de uma yeshiva (8o ano ao 3o colegial).

O princípio do projeto: **a estrutura é modelada a cada ano letivo**. Nada é fixo no código. Em cada ano, a direção define:

- quais e quantas turmas de kodesh existem (por nível, não por idade);
- quais alunos estão em cada turma;
- o rabino da turma (que dá Gemara) e os rabinos das outras matérias, que podem mudar a cada trimestre;
- os trimestres e a escala de notas.

E, a cada trimestre, cada rabino define as provas da sua matéria e quais delas aparecem no boletim.

Além disso:

- **UX e UI são prioridade.** O app tem que ser bonito e fácil de usar, no computador, no tablet e no celular. O design é feito antes das telas, não no fim.
- Cada prova pode ter o scan da prova de cada aluno, além da prova em branco e do gabarito.
- Frequência por trimestre: aulas dadas, faltas, atrasos e porcentagem de presença. Lançada à mão ou importada de Excel.
- Comentário geral e de comportamento, escritos pelo rabino da turma.
- Boletim em PDF, enviado aos pais por email depois da revisão da direção. Os pais não acessam o sistema.
- Alunos, turmas e frequência podem ser importados de planilha Excel.
- Cada ano começa vazio. Ao fechar, o ano vai para o arquivo, só para leitura.
- A turma da área laica é apenas anotada por aluno/ano, sem notas.

## 2. Decisões já tomadas

| Tema | Decisão |
|---|---|
| Idioma | Interface e boletim em português. Nomes de matérias e provas podem ter hebraico |
| UX/UI | Prioridade. Sistema visual e protótipo das telas principais antes de codar as telas |
| Visual | Azul do logo Or Yossef (#005A8E) e branco. Moderno e sóbrio, sem cara de template genérico: sem gradientes, sem emojis, sem enfeites. Paleta e tipografia na seção 6b |
| Usuários | Rabinos usam celular e computador, com familiaridade média com tecnologia |
| Tela inicial | Lista de pendências de cada usuário, com atalho direto para resolver cada uma |
| Períodos | Trimestres, criados por ano letivo (padrão 3, editável) |
| Escala | Definida por ano, padrão 0 a 10. Notas com até 1 casa decimal. Cada prova pode ter nota máxima própria |
| Notas | Várias provas por matéria no trimestre. Não existe nota final manual |
| Boletim | Cada matéria lista as provas que o rabino marcou para o boletim (ex: `Gemara: Prova 1 - 10 / Prova 2 - 6.6`). Só as notas, sem média |
| Boletim anual | Sim: além do boletim de cada trimestre, um boletim de fim de ano com os 3 trimestres |
| Recuperação e segunda chamada | É mais uma prova. O rabino escolhe o que vai para o boletim |
| Rabino da turma | Um por turma, dá Gemara e é o responsável pela turma |
| Rabinos das matérias | Cada matéria tem seu rabino, que pode mudar a cada trimestre |
| Comentários no boletim | Só o rabino da turma escreve: um comentário geral e um de comportamento por aluno por trimestre. A direção não escreve nem corrige: se precisar mudar, devolve a turma para `open` |
| Frequência | Por aluno e trimestre, uma só para a turma inteira (não por matéria): aulas dadas, faltas, atrasos e % de presença. Atraso conta como presença. Manual ou por Excel |
| Troca de turma | Permitida no meio do ano |
| Ano letivo | Nome civil (ex: 2027). Cada ano começa vazio. Ano fechado vai para o arquivo, só leitura. O cadastro do aluno continua entre os anos |
| Nomes iguais | Cada aluno tem um cadastro único no sistema. A matrícula da secretaria é opcional: pode existir para alguns alunos e não para outros. Nome igual a outro aluno sempre pede confirmação |
| Scans | Scan da prova por aluno, prova em branco e gabarito por prova. Só a equipe vê. Não vão no boletim. Os scans dos alunos ficam só até o começo do ano letivo seguinte, quando são apagados (com confirmação do admin). Prova em branco e gabarito continuam |
| Área laica | Fora do sistema de notas. Só um campo com a turma laica do aluno no ano. Boletim separado |
| Remetente do email | Configurável numa tela de configurações do admin (email e nome do remetente), não fixo no código |
| Pais | Sem acesso. Recebem o boletim em PDF por email (até dois emails por aluno) |
| Revisão | O rabino da turma marca como pronta, a direção revisa e libera. Só boletim liberado é enviado |
| Criar shiur | Botão no começo do ano: nome do shiur, rabino da turma, matérias com seus rabinos e alunos, tudo numa tela |
| Importação | Excel para alunos e turmas, e para frequência. A planilha de alunos já vem dividida por turma e rabino, e cria os shiurim e rabinos que faltam. Sempre com pré-visualização antes de aplicar |
| Prazo | Uso pleno no ano letivo de 2027. Pode ficar pronto bem antes |
| Tamanho | Cerca de 75 alunos, 6 a 7 turmas, 6 a 7 rabinos |
| Hospedagem e manutenção | Paga pela escola. Manutenção pelo desenvolvedor, remotamente |
| Senhas | Sem "esqueci a senha" no início. O admin redefine |
| Para depois | Autorizações detalhadas e features de AI |
| Hospedagem (decidido na Fase 0) | Railway, com deploy a partir do GitHub. Sem AWS |
| Ambiente local (Fase 0) | Só Python, sem Node e sem Docker no computador do desenvolvedor. Tailwind pelo `pytailwindcss`; HTMX e Alpine servidos pelo próprio app, sem CDN |
| Testes de banco (Fase 0) | Rodam no GitHub Actions contra MySQL. Sem MySQL local, são pulados no computador |
| Blueprint `main` (Fase 0) | Além dos 9 da lista: tela inicial (pendências) e `/healthz` para o monitoramento |

## 3. Stack

- Python 3.12, Flask (app factory + blueprints)
- Frontend: Jinja + **Tailwind CSS** + **HTMX** + **Alpine.js**. Interatividade de app (salvar sem recarregar, grade de notas fluida) sem precisar de um SPA
- MySQL 8 com `utf8mb4` e collation `utf8mb4_unicode_ci`
- SQLAlchemy 2 + Flask-Migrate (Alembic)
- Flask-Login, senhas com hash (argon2 ou werkzeug)
- Flask-WTF para formulários e CSRF
- WeasyPrint para PDF (exige pango e fontes no Dockerfile)
- Pillow + img2pdf para juntar fotos de scan num PDF e comprimir
- openpyxl para importar e exportar planilhas
- Arquivos (scans e documentos): S3 (boto3), com fallback para pasta local em desenvolvimento
- Email transacional (Amazon SES, Resend ou SMTP; decidir na Fase 4)
- Monitoramento: verificação de disponibilidade + alerta de erro por email (ex: Sentry no plano gratuito)
- pytest + factory_boy, **sempre contra MySQL**
- Docker + docker-compose, GitHub Actions (ruff + pytest + deploy)
- Deploy: Railway ou AWS (decidir na Fase 4)

## 4. Modelo de dados

Princípios:

1. **O aluno não tem turma fixa.** A turma existe dentro de um ano letivo, e o aluno entra nela por matrícula.
2. **O aluno é identificado pelo seu cadastro** (código interno, ou matrícula da secretaria se existir), nunca só pelo nome.
3. **Cada ano é isolado.** Turmas, matérias da turma, provas, notas e frequência pertencem a um ano. O ano novo começa vazio, e o fechado fica só para leitura.
4. **A nota pertence a uma prova**, e a prova pertence a uma matéria da turma num trimestre.
5. **Arquivos ficam no storage.** O banco guarda só a chave e os metadados.

```
users
  id, name, email (unique, nullable), password_hash (nullable até o admin ativar),
  role [admin|rabbi], is_active, created_at

students
  id,                                  -- código interno, mostrado na tela
  external_id (unique, nullable),      -- matrícula da secretaria, se existir
  first_name, last_name, hebrew_name, birth_date,
  parent_name, parent_phone, parent_email, parent_email_2,
  is_active, notes, created_at

academic_years
  id, name, start_date, end_date,
  status [active|archived],            -- só um active por vez
  grade_scale_max (DECIMAL, ex: 10.0)

terms
  id, academic_year_id, number, name, start_date, end_date, is_locked
  unique(academic_year_id, number)

student_years                          -- o aluno naquele ano
  id, student_id, academic_year_id,
  school_grade (8..12, exibido como 8o ano, 9o ano, 1o colegial, 2o colegial, 3o colegial),
  secular_class_label,                 -- ex: "9o B" (só anotação)
  notes
  unique(student_id, academic_year_id)

kodesh_classes                         -- turma de kodesh daquele ano
  id, academic_year_id, name, level,
  homeroom_rabbi_id (fk users),        -- rabino da turma (dá Gemara)
  sort_order

subjects                               -- catálogo global de matérias
  id, name, is_active, sort_order

class_subjects                         -- matéria dentro de uma turma do ano
  id, kodesh_class_id, subject_id,
  default_teacher_id (fk users, nullable),
  report_label (nullable), sort_order, is_active
  unique(kodesh_class_id, subject_id)

class_subject_terms                    -- quem dá a matéria naquele trimestre
  id, class_subject_id, term_id, teacher_id (fk users)
  unique(class_subject_id, term_id)

enrollments                            -- aluno na turma de kodesh
  id, student_year_id, kodesh_class_id, start_date, end_date (nullable)

assessments                            -- prova de uma matéria no trimestre
  id, class_subject_id, term_id, name, date (nullable),
  max_score (DECIMAL, default = grade_scale_max do ano),
  include_in_report (bool), sort_order,
  created_by, created_at

assessment_scores
  id, assessment_id, enrollment_id,
  score (DECIMAL(5,1), 0..max_score, nullable),
  status [graded|absent|exempt],
  updated_by, updated_at
  unique(assessment_id, enrollment_id)

assessment_files                       -- scans e arquivos de uma prova
  id, assessment_id,
  enrollment_id (nullable),            -- preenchido = scan da prova do aluno
  kind [student_scan|blank_exam|answer_key],
  storage_key, mime_type, size_bytes, page_count,
  uploaded_by, created_at

term_attendance                        -- frequência do aluno no trimestre
  id, enrollment_id, term_id,
  classes_held, absences, lates,
  source [manual|import], updated_by, updated_at
  unique(enrollment_id, term_id)

comments
  id, enrollment_id, term_id,
  category [general|behavior],
  visibility [public|internal], text, author_id, created_at, updated_at

class_term_status                      -- fluxo de revisão por turma e trimestre
  id, kodesh_class_id, term_id,
  status [open|ready_for_review|approved],
  submitted_by, submitted_at, approved_by, approved_at
  unique(kodesh_class_id, term_id)

report_deliveries                      -- envio do boletim por email
  id, enrollment_id, term_id, recipient_email,
  status [queued|sent|failed], error, sent_at, sent_by

documents                              -- documentos gerais do aluno
  id, student_id, academic_year_id (nullable), title, storage_key,
  mime_type, size_bytes, uploaded_by, created_at

import_batches                         -- histórico de importações de Excel
  id, academic_year_id, term_id (nullable),
  kind [students|attendance], filename, uploaded_by, created_at,
  status [preview|applied|discarded], summary_json

audit_log
  id, user_id, action, entity_type, entity_id, before_json, after_json, created_at

app_settings                           -- configurações editáveis pelo admin (ex: remetente do email)
  key (unique), value, updated_by, updated_at
```

### Regras de negócio

**Ano letivo**
- Só um ano `active` por vez. As telas do dia a dia mostram só o ano ativo.
- Criar um ano novo gera os trimestres (padrão 3). O ano começa sem turmas, matérias, provas, notas e frequência.
- Fechar o ano muda o status para `archived`: tudo daquele ano fica só para leitura e aparece na tela de arquivo.
- A escala do ano não pode mudar depois que houver notas.
- O cadastro do aluno (`students`) continua entre os anos. É ele que liga o histórico.

**Rabinos**
- Rabino da turma: `homeroom_rabbi_id`. É o responsável pela turma, pelos comentários e pela revisão.
- Rabino de uma matéria no trimestre: `class_subject_terms.teacher_id`; se não houver, `class_subjects.default_teacher_id`; se não houver, o rabino da turma.
- O boletim mostra o rabino de cada matéria naquele trimestre.

**Turmas e matrículas**
- Matéria com provas ou notas não pode ser apagada da turma: só desativada.
- Um `student_year` só pode ter uma matrícula ativa por vez. Troca de turma no meio do ano: fecha a matrícula atual e abre outra.
- Notas, scans e frequência ficam na matrícula onde foram lançados. O boletim do trimestre junta as matrículas do aluno naquele trimestre e indica a troca de turma.

**Notas**
- `score` tem até 1 casa decimal, entre 0 e o `max_score` da prova.
- `absent` e `exempt` não têm score.
- No boletim, cada matéria lista as provas com `include_in_report = true`, na ordem definida pelo rabino, com a nota como foi dada. Se o `max_score` da prova for diferente da escala do ano, aparece o máximo junto (ex: 18/20).
- Matéria sem nenhuma prova marcada não aparece no boletim daquele trimestre.
- Trimestre travado bloqueia edição de provas, notas, scans, frequência e comentários. Só o admin destrava.

**Frequência**
- Por aluno, por trimestre: aulas dadas, faltas e atrasos. Uma só para a turma, não separada por matéria.
- Presença % = (aulas dadas - faltas) / aulas dadas * 100, com 1 casa decimal. Atraso conta como presença.
- Validar: faltas e atrasos não podem passar das aulas dadas.
- Lançada à mão numa grade da turma, ou importada de Excel.

**Comentários**
- Comentários públicos: só o rabino da turma escreve. A direção não escreve nem edita. No máximo um geral e um de comportamento por aluno por trimestre.
- Anotações internas: qualquer rabino. Ilimitadas e nunca saem do sistema.

**Scans**
- Um ou mais arquivos por aluno por prova. Várias fotos enviadas de uma vez viram um único PDF.
- Aceita JPG, PNG, HEIC e PDF, com limite de tamanho em config. Imagens comprimidas antes de salvar.
- Nunca no boletim, nunca públicos. Download só por URL assinada de curta duração.

**Revisão e envio**
- Cada turma, em cada trimestre: `open` -> `ready_for_review` (rabino da turma marcou como pronta) -> `approved` (direção liberou).
- Em `ready_for_review`, só a direção edita (menos os comentários públicos), e pode devolver para `open`.
- `approved` trava o trimestre daquela turma. Só o admin reabre.
- Só boletim de turma `approved` é enviado. A pré-visualização funciona sempre, com marca d'água "rascunho".
- Um email por aluno, para os dois emails dos pais, com o PDF anexado. Cada envio fica em `report_deliveries`, e falhas podem ser reenviadas.

**Importação de Excel**
- Dois tipos: alunos e turmas do ano; frequência de um trimestre.
- A planilha de alunos vem dividida por turma e rabino. O formato exato (uma aba por turma, ou colunas de turma e rabino) será definido a partir de um exemplo real.
- Casamento do aluno: pela matrícula, se a planilha tiver. Sem matrícula, pelo nome completo (e data de nascimento, se houver). Nome que não existe vira aluno novo. Nome que bate com mais de um aluno vai para a lista de conflitos e só é aplicado com confirmação manual.
- Turma que não existe no ano aparece como "shiur novo" e é criada ao confirmar.
- Rabino que não existe aparece como "rabino novo" e é criado como usuário inativo, sem senha, para o admin ativar depois.
- Fluxo: subir o arquivo -> pré-visualização (shiurim novos, rabinos novos, alunos novos, alterados, trocas de turma, conflitos, ausentes, erros) -> confirmar -> aplicar numa única transação.
- Alunos que não estão na planilha não são desativados automaticamente.
- Troca de turma pela planilha segue a regra da troca de turma.
- Para cada tipo, o sistema oferece um modelo para baixar e uma exportação do estado atual no mesmo formato.

**Geral**
- Nada é apagado de verdade em alunos, matrículas e matérias de turma.
- Toda alteração de prova, nota, scan, frequência e comentário grava em `audit_log`.

## 5. Perfis de acesso (provisório, a detalhar depois)

| Ação | Admin | Rabino da turma | Outros rabinos |
|---|---|---|---|
| Anos, trimestres, escala, matérias, turmas, usuários | sim | não | não |
| Cadastro de alunos, matrículas, importação de Excel | sim | não | não |
| Ver todas as turmas e alunos do ano ativo e do arquivo | sim | sim | sim |
| Criar provas, lançar notas e subir scans | sim | sim | sim |
| Lançar frequência | sim | sim | sim |
| Comentários públicos (geral e comportamento) | não | sim, na sua turma | não |
| Anotações internas | sim | sim | sim |
| Marcar turma como pronta para revisão | sim | sim, na sua turma | não |
| Liberar, enviar boletins, destravar trimestre, fechar ano | sim | não | não |
| Redefinir senhas, ver audit log | sim | não | não |

---

## 6. Critérios de usabilidade

Valem para todas as fases com tela. Uma tela só está pronta quando cumpre estes critérios:

- Lançar as notas de uma prova para uma turma de 12 alunos em menos de 1 minuto, só com o teclado.
- Subir o scan de uma prova pelo celular em menos de 3 toques.
- Funciona bem em celular, tablet e computador.
- Feito para quem não tem muita familiaridade com tecnologia: textos claros, poucas opções por tela, botões grandes, nada importante escondido em menus.
- Toda ação mostra retorno claro: salvo, erro, o que falta.
- Nenhuma ação destrutiva sem confirmação.
- Testada com o seu pai e com pelo menos um rabino antes de marcar a fase como concluída.

---

## 6b. Identidade visual (Or Yossef Yeshiva College)

Cores tiradas do logo:

| Token | Cor | Uso |
|---|---|---|
| `primary` | `#005A8E` | Azul do logo. Botões principais, links, cabeçalho, destaques. Contraste 7.4:1 sobre branco |
| `primary-dark` | `#00466F` | Hover e texto de títulos |
| `primary-light` | `#E6F0F6` | Fundo de linha selecionada, aba ativa, áreas de destaque |
| `gray` | `#6E6E6E` | Cinza do logo. Texto secundário, rótulos |
| `text` | `#1F2933` | Texto principal |
| `border` | `#DDE3E8` | Bordas e divisórias |
| `surface` | `#F7F9FA` | Fundo de áreas e cartões |
| `background` | `#FFFFFF` | Fundo da página |
| `success` | `#2E7D4F` | Salvo, liberado |
| `warning` | `#B7791F` | Pendente, faltando |
| `danger` | `#B42318` | Erro, ação destrutiva |

Regras:
- O azul é para o que importa: ação principal, navegação ativa, cabeçalho. O resto é branco e cinza.
- Cores de status sempre acompanhadas de texto ou ícone, nunca só a cor.
- Tipografia: Montserrat (geométrica, conversa com o logo) só em títulos. IBM Plex Sans no corpo e nas tabelas. IBM Plex Sans Hebrew para textos em hebraico.
- Números nas grades de notas com algarismos tabulares, alinhados.
- Cantos levemente arredondados (4 a 6px), sombras quase imperceptíveis, bastante espaço em branco.
- O padrão de "Y" espalhados do logo pode aparecer, discreto, na tela de login e no cabeçalho do boletim. Em nenhum outro lugar.

---

## 7. Fases

### Fase 0: Setup
- [x] Estrutura: `app/` com app factory, `config.py`, `app/services/`, blueprints vazios (`auth`, `admin`, `students`, `classes`, `grades`, `attendance`, `files`, `imports`, `reports`)
- [x] `docker-compose.yml` com app, MySQL e MySQL de teste, todos em `utf8mb4_unicode_ci`
- [x] `.env.example`, Flask-Migrate, pytest contra MySQL, ruff
- [x] Tailwind (build no Docker), HTMX e Alpine.js
- [x] GitHub Actions com ruff + pytest
- [x] Teste que grava e lê do banco texto com acentos e com hebraico

### Fase 1: Design e protótipo
- [ ] Identidade visual da seção 6b configurada no Tailwind (cores, fontes, espaçamentos) e componentes (botões, tabelas, formulários, alertas, modais)
- [ ] Logo em SVG (pedir o original à escola ou vetorizar o PNG)
- [ ] Protótipo navegável das telas principais: tela inicial com pendências (rabino e direção), shiur, grade de notas, scan pelo celular, frequência, boletim
- [ ] Revisão do protótipo com o seu pai e um rabino, e ajustes
- [ ] Biblioteca de componentes Jinja (macros) baseada no protótipo

**Pronto quando:** o protótipo foi aprovado e os componentes estão prontos para uso.

### Fase 2a: Modelos e migração
- [ ] Modelos SQLAlchemy da seção 4, com constraints, FKs e enums
- [ ] Migração inicial

### Fase 2b: Regras de domínio
- [ ] `app/services/`: rabino efetivo da matéria, matrícula ativa, troca de turma, porcentagem de presença, conteúdo do boletim, travamento, limite de comentários, ano ativo e arquivado
- [ ] Testes para cada regra da seção 4

### Fase 2c: Seed
- [ ] `flask seed`: 1 ano ativo e 1 arquivado, 3 trimestres, 6 turmas, 75 alunos (com dois de nome igual), matérias, rabinos trocando de matéria entre trimestres, 2 a 4 provas por matéria, notas com decimal, ausentes, frequência, uma troca de turma

### Fase 3: Autenticação e permissões
- [ ] Login/logout, `flask create-admin`, CRUD de usuários, redefinição de senha pelo admin
- [ ] Permissões da seção 5
- [ ] Testes de acesso por perfil

### Fase 4: Deploy inicial
- [ ] Decidir Railway ou AWS
- [ ] Dockerfile de produção (gunicorn, pango, fontes, Tailwind compilado)
- [ ] HTTPS, variáveis de ambiente, bucket S3 privado
- [ ] Backup diário do MySQL com retenção, e um teste de restauração
- [ ] Email configurado (domínio, SPF, DKIM)
- [ ] Monitoramento e alerta de erro por email
- [ ] Deploy automático pela branch main

A partir daqui, cada fase termina com deploy.

### Fase 5: Cadastros (admin)
- [ ] Anos letivos: criar, trimestres, escala
- [ ] Catálogo de matérias
- [ ] Alunos: CRUD, busca por nome e por matrícula
- [ ] Botão "Inserir aluno" na lista geral: cadastra e permite escolher o shiur na hora ou deixar sem shiur
- [ ] Turmas do ano: nome, nível, rabino da turma
- [ ] Matérias da turma: rabino padrão, rabino por trimestre, nome no boletim, ordem, desativar

### Fase 6: Montagem do ano
- [ ] Botão "Criar shiur": assistente numa tela só, com nome e nível, rabino da turma (escolher ou cadastrar na hora), matérias com seus rabinos e alunos (buscar existentes, cadastrar novos ou colar uma lista de nomes)
- [ ] Aviso de nome igual a um aluno já cadastrado, pedindo confirmação
- [ ] Tela do shiur: botão "Inserir aluno" (buscar existente ou cadastrar novo, já entrando no shiur) e remover aluno
- [ ] Série escolar e turma laica do aluno no ano
- [ ] Troca de turma no meio do ano
- [ ] Lista de alunos sem turma no ano ativo

### Fase 7: Importação de Excel: alunos e turmas
- [ ] Ler o formato real da planilha da escola (dividida por turma e rabino) e oferecer um modelo no mesmo formato
- [ ] Criar shiurim e rabinos que faltam, a partir da pré-visualização
- [ ] Tela de conflitos: escolher se o nome é um aluno existente ou um aluno novo
- [ ] Upload, validação linha a linha e pré-visualização
- [ ] Aplicar numa única transação e registrar em `import_batches`
- [ ] Exportar o estado atual no mesmo formato
- [ ] Testes: shiur novo, rabino novo, nomes iguais, aluno sem matrícula, reimportar a mesma planilha não muda nada

### Fase 8: Provas e notas
- [ ] Tela da matéria no trimestre: criar, renomear, ordenar e apagar provas (apagar só sem notas e sem scans), nota máxima, "aparece no boletim"
- [ ] Grade de lançamento: alunos nas linhas, provas nas colunas, salvamento automático (HTMX), navegação por teclado, vírgula ou ponto como decimal, ausente/dispensado
- [ ] Bloqueio por trimestre travado
- [ ] Audit log
- [ ] Testes do fluxo e critérios de usabilidade

### Fase 9: Scans das provas
- [ ] Upload do scan por aluno direto da grade de notas
- [ ] Upload pelo celular com a câmera, várias fotos de uma vez, juntadas num PDF
- [ ] Prova em branco e gabarito na tela da prova
- [ ] Visualização e download por URL assinada
- [ ] Indicador na grade: quem tem scan e quem não tem
- [ ] Testes: tipos aceitos, limite de tamanho, permissões, trimestre travado

### Fase 10: Frequência
- [ ] Grade da turma no trimestre: aulas dadas, faltas e atrasos por aluno, com a % calculada ao vivo
- [ ] Importação de Excel de frequência (aluno, aulas dadas, faltas, atrasos), com o mesmo casamento de alunos e pré-visualização
- [ ] Modelo para download e exportação no mesmo formato
- [ ] Testes: validação, cálculo da %, importação

### Fase 11: Comentários
- [ ] Comentário geral e de comportamento por aluno, só para o rabino da turma
- [ ] Anotações internas para todos os rabinos
- [ ] Testes de permissão, limite e visibilidade

### Fase 12: Boletim em PDF
- [ ] Template em português seguindo a identidade visual: logo, aluno, série, turma, rabino da turma, trimestre
- [ ] Cada matéria com o rabino do trimestre e a lista de provas marcadas
- [ ] Frequência: aulas, faltas, atrasos e % de presença
- [ ] Comentário geral e de comportamento
- [ ] Marca d'água "rascunho" enquanto a turma não estiver liberada
- [ ] Caso de troca de turma no trimestre
- [ ] Botão por aluno e "gerar todos da turma"
- [ ] Boletim anual: os 3 trimestres do aluno num PDF só
- [ ] Testes: anotações internas e scans nunca aparecem

### Fase 13: Revisão e envio por email
- [ ] Rabino da turma marca como pronta, direção revisa, devolve ou libera
- [ ] Painel da direção com o status de todas as turmas no trimestre
- [ ] Tela de configurações do admin: email e nome do remetente
- [ ] Envio por email em fila, com o PDF anexado, registro e reenvio de falhas
- [ ] Testes: permissões, bloqueio de edição, envio só de turma liberada

**Marco: MVP completo.**

### Fase 14: Documentos gerais
- [ ] Upload por aluno e listagem por aluno e por ano

### Fase 14b: Tela inicial com pendências
- [ ] Rabino: provas sem nota, provas sem scan, frequência não lançada, comentários faltando, dias até o fim do trimestre, botão "marcar shiur como pronto" quando tudo estiver completo
- [ ] Direção: status de cada shiur no trimestre, shiurim atrasados, rabinos sem acesso ativado
- [ ] Cada pendência leva direto à tela onde se resolve

### Fase 15: Arquivo e histórico
- [ ] Fechar o ano: confirmação, verificação de pendências (turmas não liberadas), status `archived`
- [ ] Tela de arquivo: anos fechados, só leitura, com turmas, notas, frequência e boletins
- [ ] Ficha do aluno com o histórico de todos os anos, ligada pela matrícula
- [ ] Visão por turma: status de lançamento (provas sem nota, alunos sem scan, frequência faltando)

### Fase 16: Abertura do ano novo
- [ ] Criar o ano novo vazio
- [ ] Apagar os scans dos alunos do ano anterior, com confirmação do admin (prova em branco e gabarito ficam)
- [ ] Opção de copiar a estrutura do ano anterior (turmas, matérias, rabinos) como ponto de partida, tudo editável
- [ ] Distribuir os alunos pela tela ou pela importação de Excel
- [ ] Avançar a série escolar e marcar formandos como inativos

### Fase 17: Relatórios
- [ ] Notas por turma, matéria e trimestre
- [ ] Frequência por turma
- [ ] Exportar para Excel

### Fases opcionais
- [ ] Scans em lote: subir um PDF com as provas da turma e distribuir as páginas entre os alunos
- [ ] Exceções de matéria por aluno, se existir aluno com matérias diferentes da turma
- [ ] Chamada diária, se o total por trimestre não bastar
- [ ] Autorizações detalhadas (a definir)
- [ ] Features de AI (a definir)

---

## 8. Pendências para confirmar com a direção

- Um exemplo real da planilha de alunos (pode ser com nomes trocados), para definir o formato da importação. Virá depois; até lá, formato provisório
- Logo: usar `assets/logo.webp` (vetorizar na Fase 1). Cabeçalho oficial e assinatura no boletim: a definir
- Endereço que envia os emails: definido pelo admin na tela de configurações, perto do envio
- LGPD: comunicação aos pais sobre os dados guardados. Não por ora, mas obrigatório antes de entrar dado real

## 9. Como trabalhar com o Claude Code

- Uma fase por sessão. Começar com: `Leia PLAN.md e CLAUDE.md. Vamos fazer a Fase N. Faça um plano antes de codar.`
- Revisar o plano no modo de planejamento antes de qualquer código.
- Em fases com tela, pedir para seguir os componentes da Fase 1 e checar os critérios da seção 6.
- Um commit por item de checklist, com testes passando.
- Ao terminar a fase, marcar os checkboxes e registrar decisões novas na seção 2.
- Se uma regra de negócio mudar, atualizar o PLAN.md primeiro e só depois o código.
