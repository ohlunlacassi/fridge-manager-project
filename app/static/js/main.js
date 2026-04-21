// ── Password match validation (register page) ──
const passwordInput = document.getElementById("password");
const confirmInput = document.getElementById("confirm_password");
const confirmError = document.getElementById("confirm-error");

function validatePasswords() {
  if (!passwordInput || !confirmInput) return;
  const password = passwordInput.value;
  const confirm = confirmInput.value;
  if (confirm.length === 0) {
    confirmError.textContent = "";
    return;
  }
  if (password !== confirm) {
    confirmError.textContent = "Passwords do not match.";
  } else {
    confirmError.textContent = "";
  }
}

if (passwordInput) passwordInput.addEventListener("input", validatePasswords);
if (confirmInput) confirmInput.addEventListener("input", validatePasswords);

// ── Hide flash messages when user starts editing any input field ──
const inputs = document.querySelectorAll(".form-group input");
inputs.forEach((input) => {
  input.addEventListener("input", () => {
    document.querySelectorAll(".alert").forEach((alert) => {
      alert.style.display = "none";
    });
  });
});

// ── Add Ingredient Modal ──
const modalOverlay = document.getElementById("modal-overlay");
const openBtn = document.getElementById("open-add-modal");
const openBtnEmpty = document.getElementById("open-add-modal-empty");
const closeBtn = document.getElementById("close-modal");

function openModal() {
  if (modalOverlay) modalOverlay.classList.add("open");
}

function closeModal() {
  if (modalOverlay) modalOverlay.classList.remove("open");
}

if (openBtn) openBtn.addEventListener("click", openModal);
if (openBtnEmpty) openBtnEmpty.addEventListener("click", openModal);
if (closeBtn) closeBtn.addEventListener("click", closeModal);

// Close modal when clicking outside the modal box.
if (modalOverlay) {
  modalOverlay.addEventListener("click", (e) => {
    if (e.target === modalOverlay) closeModal();
  });
}

// ── Quantity +/- buttons in modal ──
const qtyInput = document.getElementById("quantity");
const qtyMinus = document.getElementById("qty-minus");
const qtyPlus = document.getElementById("qty-plus");

if (qtyMinus && qtyInput) {
  qtyMinus.addEventListener("click", () => {
    const val = parseFloat(qtyInput.value) || 1;
    if (val > 1) qtyInput.value = Math.round((val - 1) * 100) / 100;
  });
}

if (qtyPlus && qtyInput) {
  qtyPlus.addEventListener("click", () => {
    const val = parseFloat(qtyInput.value) || 0;
    qtyInput.value = Math.round((val + 1) * 100) / 100;
  });
}

// ── Filter tabs — show/hide ingredient cards by category ──
const filterTabs = document.querySelectorAll(".filter-tab");
const ingredientCards = document.querySelectorAll(".ingredient-card");

filterTabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    // Update active tab.
    filterTabs.forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");

    const category = tab.dataset.category;
    ingredientCards.forEach((card) => {
      if (category === "all" || card.dataset.category === category) {
        card.style.display = "";
      } else {
        card.style.display = "none";
      }
    });
  });
});

// ── Search — filter cards by name in real-time ──
const searchInput = document.getElementById("ingredient-search");

if (searchInput) {
  searchInput.addEventListener("input", () => {
    const query = searchInput.value.toLowerCase();
    ingredientCards.forEach((card) => {
      const name = card.dataset.name || "";
      card.style.display = name.includes(query) ? "" : "none";
    });
  });
}

// ── Auto-dismiss flash messages after 3 seconds ──
document.querySelectorAll(".alert").forEach((alert) => {
  setTimeout(() => {
    alert.style.transition = "opacity 0.5s ease";
    alert.style.opacity = "0";
    setTimeout(() => alert.remove(), 500);
  }, 3000);
});
