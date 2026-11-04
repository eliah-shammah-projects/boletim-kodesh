// Grade de notas: navegação por teclado, validação e salvamento automático.
//
// Cada campo de nota tem: data-row, data-col, data-max. O estado visual fica em
// data-state no elemento pai (.group): "" | "saving" | "saved" | "error".
//
// Opções do componente:
//   saveUrl: URL para salvar (POST). Sem saveUrl (protótipo), o salvamento é simulado.

(function () {
  const ABSENT = "Ausente";
  const EXEMPT = "Dispensado";

  // Devolve {kind, value, display} ou {error}.
  function parseScore(raw, max) {
    const text = raw.trim();
    if (text === "") return { kind: "empty", value: null, display: "" };
    const lower = text.toLowerCase();
    if (lower === "a" || lower === ABSENT.toLowerCase()) return { kind: "absent", value: null, display: ABSENT };
    if (lower === "d" || lower === EXEMPT.toLowerCase()) return { kind: "exempt", value: null, display: EXEMPT };
    if (!/^\d{1,3}([.,]\d)?$/.test(text)) {
      return { error: "Use um número com até 1 casa (ex: 8,5), A ou D." };
    }
    const value = Number(text.replace(",", "."));
    if (value > max) return { error: `A nota máxima desta prova é ${String(max).replace(".", ",")}.` };
    const display = String(value).replace(".", ",");
    return { kind: "graded", value, display };
  }
  window.parseScore = parseScore;

  document.addEventListener("alpine:init", () => {
    window.Alpine.data("gradeGrid", (options = {}) => ({
      col: 0,
      pending: 0,
      errors: 0,

      init() {
        this.$el.addEventListener("keydown", (event) => this.onKeydown(event));
        this.$el.addEventListener("change", (event) => this.onChange(event));
        this.$el.addEventListener("focusin", (event) => {
          if (event.target.matches("[data-row]")) event.target.select();
        });
      },

      get statusText() {
        if (this.errors > 0) return this.errors === 1 ? "1 nota com erro, não salva" : `${this.errors} notas com erro, não salvas`;
        if (this.pending > 0) return "Salvando…";
        return "Todas as notas estão salvas";
      },

      cell(row, col) {
        return this.$el.querySelector(`[data-row="${row}"][data-col="${col}"]`);
      },

      onKeydown(event) {
        const input = event.target;
        if (!input.matches("[data-row]")) return;
        const row = Number(input.dataset.row);
        const col = Number(input.dataset.col);
        let next = null;
        if (event.key === "Enter" || event.key === "ArrowDown") next = this.cell(row + 1, col);
        else if (event.key === "ArrowUp") next = this.cell(row - 1, col);
        else return;
        event.preventDefault();
        if (event.key === "Enter") this.commit(input);
        if (next) next.focus();
        else if (event.key === "Enter") input.blur();
      },

      onChange(event) {
        if (event.target.matches("[data-row]")) this.commit(event.target);
      },

      setState(input, state, message = "") {
        const box = input.closest(".group");
        const before = box.dataset.state;
        if (before === "error") this.errors--;
        if (state === "error") this.errors++;
        box.dataset.state = state;
        input.setAttribute("aria-invalid", state === "error" ? "true" : "false");
        const err = box.querySelector("[data-error]");
        if (err) err.textContent = message;
      },

      commit(input) {
        if (input.value === input.dataset.saved) {
          if (input.closest(".group").dataset.state === "error") this.setState(input, "");
          return;
        }
        const result = parseScore(input.value, Number(input.dataset.max));
        if (result.error) {
          this.setState(input, "error", result.error);
          return;
        }
        input.value = result.display;
        this.setState(input, "saving");
        this.pending++;
        this.save(input, result).then(
          () => {
            input.dataset.saved = result.display;
            this.setState(input, "saved");
          },
          () => {
            this.setState(input, "error", "Não foi possível salvar. Tente de novo.");
          },
        ).finally(() => {
          this.pending--;
        });
      },

      save(input, result) {
        if (!options.saveUrl) {
          return new Promise((resolve) => setTimeout(resolve, 350));
        }
        const body = new URLSearchParams({
          enrollment: input.dataset.enrollment,
          assessment: input.dataset.assessment,
          kind: result.kind,
          score: result.value ?? "",
        });
        const token = document.querySelector("body").getAttribute("hx-headers");
        return fetch(options.saveUrl, {
          method: "POST",
          headers: { "X-CSRFToken": JSON.parse(token)["X-CSRFToken"] },
          body,
        }).then((response) => {
          if (!response.ok) throw new Error(String(response.status));
        });
      },
    }));
  });
})();
