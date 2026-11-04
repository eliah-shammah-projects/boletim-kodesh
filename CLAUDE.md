# CLAUDE.md

Sistema de notas de kodesh de uma yeshiva. Plano completo e modelo de dados em `PLAN.md`. Leia antes de qualquer tarefa.

## Regras do projeto

- Seguir o modelo de dados do `PLAN.md`. Não criar tabelas ou campos novos sem perguntar.
- A estrutura é definida por ano letivo: turmas, matérias, rabinos, trimestres e escala vêm do banco, nunca do código.
- Cada ano é isolado. Só um ano `active`. Ano `archived` é só leitura.
- O aluno é identificado pelo cadastro (id, ou `external_id` se existir), nunca só pelo nome. Nome igual a outro aluno sempre pede confirmação.
- O aluno nunca tem turma fixa. A ligação é sempre via `enrollments`.
- Rabino efetivo da matéria: `class_subject_terms` -> `class_subjects.default_teacher_id` -> `homeroom_rabbi_id`.
- A nota pertence a uma prova. Decimal com até 1 casa, entre 0 e o `max_score` da prova.
- O boletim lista, por matéria, as provas com `include_in_report = true`. Não existe nota final manual.
- Comentários públicos (geral e comportamento): só o rabino da turma e o admin, no máximo um de cada por aluno por trimestre.
- Trimestre travado bloqueia edição de provas, notas, scans, frequência e comentários.
- Revisão por turma e trimestre: `open` -> `ready_for_review` -> `approved`. Email só para turma `approved`.
- Importação de Excel: sempre pré-visualização antes de aplicar, uma única transação, nunca desativar aluno automaticamente. Shiurim e rabinos novos só são criados ao confirmar a pré-visualização.
- Arquivos no storage, acessados só por URL assinada. Scans e anotações internas nunca vão para o boletim.
- Toda alteração de prova, nota, scan, frequência e comentário grava em `audit_log`.
- Não apagar alunos, matrículas nem matérias de turma: usar `is_active` / `end_date`.

## UX e UI

- UX e UI são prioridade. Usar sempre os componentes (macros Jinja) da Fase 1. Não criar estilos avulsos.
- Cores e fontes só pelos tokens da seção 6b do PLAN.md (azul do logo `#005A8E`). Sem gradientes, sem emojis, sem enfeites.
- Toda tela funciona em celular, tablet e computador.
- Toda ação dá retorno claro (salvo, erro, o que falta). Ação destrutiva sempre pede confirmação.
- Conferir os critérios de usabilidade da seção 6 do PLAN.md antes de concluir uma tela.

## Código

- Python 3.12, Flask com app factory e blueprints.
- Frontend: Jinja + Tailwind + HTMX + Alpine.js. Sem SPA.
- SQLAlchemy 2 (estilo `select()`), migrações com Flask-Migrate. Nunca alterar o banco sem migração.
- MySQL em `utf8mb4_unicode_ci`. Notas como `Decimal`, nunca `float`.
- Lógica de negócio em `app/services/`, não nas rotas nem nos templates.
- Nomes de código em inglês. Interface e boletim em português.
- Formulários com Flask-WTF e CSRF. Segredos só em variáveis de ambiente.

## Testes e qualidade

- Testes sempre contra MySQL, nunca SQLite. Nunca enviar email de verdade nos testes.
- Toda regra de negócio tem teste em pytest.
- Antes de concluir uma tarefa: `ruff check .` e `pytest` passando.
- Um commit por item do checklist do PLAN.md.

## Comandos

- Local (sem Docker): `.venv/Scripts/ruff check .`, `.venv/Scripts/pytest` (testes de banco são pulados sem MySQL e rodam no GitHub Actions)
- CSS: `tailwindcss -i app/static/src/app.css -o app/static/dist/app.css --minify` (com `TAILWINDCSS_VERSION=v4.3.4`)
- `docker compose up` sobe app + MySQL (onde houver Docker, ex: CI)
- `flask db migrate -m "..."` / `flask db upgrade`
- `flask seed` dados fictícios
- `flask create-admin`
- `pytest`

## Fluxo

- Antes de codar uma fase, apresentar um plano e esperar aprovação.
- Ao terminar, marcar os checkboxes da fase no PLAN.md.
- Dados de alunos são de menores: nunca logar notas, comentários, nomes de arquivos ou dados pessoais.
