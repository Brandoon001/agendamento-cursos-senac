document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-dismiss]").forEach((button) => {
    button.addEventListener("click", () => {
      button.closest(".flash")?.remove();
    });
  });

  const seletorTipo = document.querySelector("[data-tipo-curso]");
  if (seletorTipo) {
    const camposPagos = document.querySelectorAll("[data-campo-pago]");

    const atualizarCampos = () => {
      const pago = seletorTipo.value === "pago";
      camposPagos.forEach((campo) => {
        campo.hidden = !pago;
        campo.querySelectorAll("input").forEach((input) => {
          input.disabled = !pago;
        });
      });
    };

    atualizarCampos();
    seletorTipo.addEventListener("change", atualizarCampos);
  }
});
