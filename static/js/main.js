document.querySelectorAll("[data-copy-target]").forEach((button) => {
  button.addEventListener("click", async () => {
    const id = button.getAttribute("data-copy-target");
    const target = document.getElementById(id);
    if (!target) return;
    try {
      await navigator.clipboard.writeText(target.value || target.textContent || "");
      button.textContent = "Copiado!";
      setTimeout(() => {
        button.textContent = id === "pix-code" ? "Copiar codigo PIX" : "Copiar link";
      }, 1500);
    } catch (error) {
      button.textContent = "Nao foi possivel copiar";
    }
  });
});

const pageLoadingIndicator = document.getElementById("page-loading-indicator");

const showPageLoading = () => {
  if (pageLoadingIndicator) {
    pageLoadingIndicator.classList.remove("hidden");
  }
};

const hidePageLoading = () => {
  if (pageLoadingIndicator) {
    pageLoadingIndicator.classList.add("hidden");
  }
};

window.addEventListener("pageshow", hidePageLoading);

document.querySelectorAll("a[href]").forEach((link) => {
  link.addEventListener("click", () => {
    const href = link.getAttribute("href") || "";
    const target = link.getAttribute("target");
    const isHash = href.startsWith("#");
    const isExternal = href.startsWith("http://") || href.startsWith("https://");
    if (!href || isHash || target === "_blank" || isExternal) return;
    showPageLoading();
  });
});

document.querySelectorAll("form").forEach((form) => {
  form.addEventListener("submit", (event) => {
    if (form.dataset.submitting === "true") {
      event.preventDefault();
      return;
    }
    form.dataset.submitting = "true";
    showPageLoading();

    const submitter =
      event.submitter ||
      form.querySelector('button[type="submit"]') ||
      form.querySelector("button:not([type])");
    const loadingText = submitter?.dataset.loadingText || "Carregando...";

    form.querySelectorAll('button[type="submit"], button:not([type])').forEach((button) => {
      button.disabled = true;
      button.classList.add("opacity-70", "cursor-not-allowed");
    });

    if (submitter) {
      submitter.innerHTML =
        '<span class="inline-block h-4 w-4 animate-spin rounded-full border-2 border-current/35 border-t-current"></span>' +
        `<span>${loadingText}</span>`;
      submitter.classList.add("inline-flex", "items-center", "justify-center", "gap-2");
    }
  });
});

const messageInput = document.getElementById("id_message");
const charCounter = document.getElementById("char-count");
if (messageInput && charCounter) {
  const updateCount = () => {
    charCounter.textContent = String(messageInput.value.length);
  };
  messageInput.addEventListener("input", updateCount);
  updateCount();
}

const photosInput = document.getElementById("id_photos");
const previewGrid = document.getElementById("preview-grid");
const photosFeedback = document.getElementById("photos-feedback");
if (photosInput && previewGrid) {
  photosInput.addEventListener("change", (event) => {
    const files = Array.from(event.target.files || []);
    previewGrid.innerHTML = "";

    files.forEach((file) => {
      const image = document.createElement("img");
      image.className = "h-36 w-full rounded-2xl object-cover";
      image.alt = "Previa";
      image.src = URL.createObjectURL(file);
      previewGrid.appendChild(image);
    });

    if (photosFeedback) {
      photosFeedback.textContent = files.length
        ? `${files.length} foto(s) selecionada(s). Toque em Continuar para salvar.`
        : "";
    }
  });
}

const items = [
  "Aniversario de namoro",
  "Dia dos Namorados",
  "Pedido de desculpas",
  "Surpresa romantica",
  "Aniversario de casamento",
  "Amor a distancia",
  "Pedido de casamento",
  "Reconciliacao",
  "Votos",
  "Agradecimento",
  "Primeiro encontro",
  "So porque sim",
];

const track = document.getElementById("chipsTrack");
if (track) {
  const makeChip = (txt) => {
    const el = document.createElement("span");
    el.className =
      "rounded-full border border-white/10 bg-base-200/40 px-3 py-1 text-xs font-semibold text-white/70 transition hover:border-love-200/40 hover:text-white";
    el.textContent = txt;
    return el;
  };

  const full = [...items, ...items];
  full.forEach((value) => track.appendChild(makeChip(value)));
}
