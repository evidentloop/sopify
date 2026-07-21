(function () {
  "use strict";

  async function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      try {
        await navigator.clipboard.writeText(text);
        return;
      } catch (error) {
        // Permission may be denied even when the API exists; use the local fallback.
      }
    }

    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.select();
    const copied = document.execCommand("copy");
    textarea.remove();

    if (!copied) {
      throw new Error("Copy command was not available");
    }
  }

  document.querySelectorAll("[data-copy-target]").forEach(function (button) {
    const defaultLabel = button.textContent.trim();
    const successLabel = button.getAttribute("data-copy-success") || "Copied";
    const errorLabel = button.getAttribute("data-copy-error") || "Select command";

    button.addEventListener("click", async function () {
      const target = document.getElementById(button.getAttribute("data-copy-target"));
      if (!target) {
        return;
      }

      try {
        await copyText(target.textContent.trim());
        button.textContent = successLabel;
      } catch (error) {
        button.textContent = errorLabel;
      }

      window.setTimeout(function () {
        button.textContent = defaultLabel;
      }, 1800);
    });
  });
})();
