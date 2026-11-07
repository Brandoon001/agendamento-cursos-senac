document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-dismiss]").forEach((button) => {
    button.addEventListener("click", () => {
      button.closest(".flash")?.remove();
    });
  });
});
