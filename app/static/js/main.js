document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-dismiss]").forEach((button) => {
    button.addEventListener("click", () => {
      button.closest(".flash")?.remove();
    });
  });

  const somenteNumeros = (valor) => valor.replace(/\D/g, "");

  const aplicarMascaraCpf = (valor) => {
    const numeros = somenteNumeros(valor).slice(0, 11);
    return numeros
      .replace(/(\d{3})(\d)/, "$1.$2")
      .replace(/(\d{3})(\d)/, "$1.$2")
      .replace(/(\d{3})(\d{1,2})$/, "$1-$2");
  };

  const aplicarMascaraTelefone = (valor) => {
    const numeros = somenteNumeros(valor).slice(0, 11);
    if (numeros.length <= 10) {
      return numeros
        .replace(/(\d{2})(\d)/, "($1) $2")
        .replace(/(\d{4})(\d)/, "$1-$2");
    }
    return numeros
      .replace(/(\d{2})(\d)/, "($1) $2")
      .replace(/(\d{5})(\d)/, "$1-$2");
  };

  document.querySelectorAll('[data-mask="cpf"]').forEach((campo) => {
    campo.addEventListener("input", () => {
      campo.value = aplicarMascaraCpf(campo.value);
    });
  });

  document.querySelectorAll('[data-mask="telefone"]').forEach((campo) => {
    campo.addEventListener("input", () => {
      campo.value = aplicarMascaraTelefone(campo.value);
    });
  });
});