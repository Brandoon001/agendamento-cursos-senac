// Comportamentos compartilhados pelas páginas públicas e administrativas.
document.addEventListener("DOMContentLoaded", () => {
  // Fecha a mensagem flash ao clicar no botão data-dismiss.
  document.querySelectorAll("[data-dismiss]").forEach((button) => {
    button.addEventListener("click", () => {
      button.closest(".flash")?.remove();
    });
  });

  // Remove automaticamente mensagens de sucesso após 7 segundos.
  document.querySelectorAll(".flash--success").forEach((flash) => {
    window.setTimeout(() => flash.remove(), 7000);
  });

  // Confirma ações marcadas em data-confirm; usa SweetAlert2 com fallback para window.confirm.
  document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (form.dataset.confirmed === "true") return;

      event.preventDefault();
      const mensagem = form.dataset.confirm;

      const enviar = () => {
        form.dataset.confirmed = "true";
        if (typeof form.requestSubmit === "function") {
          form.requestSubmit();
        } else {
          form.submit();
        }
      };

      if (typeof Swal === "undefined") {
        if (window.confirm(mensagem)) enviar();
        return;
      }

      Swal.fire({
        icon: "warning",
        title: "Confirmar ação",
        text: mensagem,
        showCancelButton: true,
        confirmButtonText: "Confirmar",
        cancelButtonText: "Cancelar",
        confirmButtonColor: "#004a8d",
        cancelButtonColor: "#686a6c",
        reverseButtons: true,
        focusCancel: true,
      }).then((resultado) => {
        if (resultado.isConfirmed) enviar();
      });
    });
  });

  // Máscaras de CPF e telefone aplicadas enquanto o usuário digita.
  const somenteDigitos = (valor) => valor.replace(/\D/g, "");

  const formatarCpf = (valor) =>
    somenteDigitos(valor)
      .slice(0, 11)
      .replace(/(\d{3})(\d)/, "$1.$2")
      .replace(/(\d{3})\.(\d{3})(\d)/, "$1.$2.$3")
      .replace(/\.(\d{3})(\d)/, ".$1-$2");

  const formatarTelefone = (valor) => {
    const digitos = somenteDigitos(valor).slice(0, 11);
    if (digitos.length > 10) {
      return digitos
        .replace(/(\d{2})(\d)/, "($1) $2")
        .replace(/(\d{5})(\d)/, "$1-$2");
    }
    return digitos
      .replace(/(\d{2})(\d)/, "($1) $2")
      .replace(/(\d{4})(\d)/, "$1-$2");
  };

  // CPF: 000.000.000-00.
  document.querySelectorAll("input[data-mask='cpf']").forEach((input) => {
    input.addEventListener("input", () => {
      input.value = formatarCpf(input.value);
    });
  });

  // Telefone: (00) 0000-0000 ou (00) 00000-0000.
  document.querySelectorAll("input[data-mask='telefone']").forEach((input) => {
    input.addEventListener("input", () => {
      input.value = formatarTelefone(input.value);
    });
  });
});
