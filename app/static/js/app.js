// Comportamentos comuns a todas as telas. Carregado antes do Alpine.

// Abrir janelas de confirmação: <button data-open-dialog="id">
document.addEventListener("click", (event) => {
  const opener = event.target.closest("[data-open-dialog]");
  if (!opener) return;
  const dialog = document.getElementById(opener.dataset.openDialog);
  if (dialog) dialog.showModal();
});

// Avisos rápidos ("Salvo", "Erro"). Disparar com:
//   window.dispatchEvent(new CustomEvent("notify", {detail: {kind: "success", message: "Salvo"}}))
// ou pelo servidor, no HTMX: cabeçalho HX-Trigger: {"notify": {"kind": "...", "message": "..."}}
document.addEventListener("alpine:init", () => {
  window.Alpine.data("toasts", () => ({
    items: [],
    nextId: 1,
    add(detail) {
      const id = this.nextId++;
      const kind = detail.kind || "success";
      this.items.push({ id, kind, message: detail.message });
      // Erros ficam até a pessoa fechar; o resto some sozinho.
      if (kind !== "danger") setTimeout(() => this.remove(id), 4000);
    },
    remove(id) {
      this.items = this.items.filter((item) => item.id !== id);
    },
  }));
});

// Erro de rede ou do servidor em qualquer requisição HTMX vira aviso visível.
document.addEventListener("htmx:responseError", () => {
  window.dispatchEvent(new CustomEvent("notify", {
    detail: { kind: "danger", message: "Não foi possível salvar. Tente de novo." },
  }));
});
document.addEventListener("htmx:sendError", () => {
  window.dispatchEvent(new CustomEvent("notify", {
    detail: { kind: "danger", message: "Sem conexão. Verifique a internet e tente de novo." },
  }));
});
