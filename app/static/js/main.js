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

// ─── Edit Ingredient Modal ───────────────────────────────────────────────────

const editModal = document.getElementById("edit-modal");
const editForm = document.getElementById("edit-form");

if (editModal && editForm) {
  document.querySelectorAll(".btn-edit-ingredient").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.getElementById("edit-name").value = btn.dataset.name;
      document.getElementById("edit-quantity").value = parseFloat(
        btn.dataset.quantity,
      );
      document.getElementById("edit-expiry").value = btn.dataset.expiry;

      setSelectValue("edit-unit", btn.dataset.unit);
      setSelectValue("edit-category", btn.dataset.category);

      editForm.action = btn.dataset.url;
      editModal.classList.add("open");
    });
  });

  document.getElementById("edit-cancel-btn").addEventListener("click", () => {
    editModal.classList.remove("open");
  });

  editModal.addEventListener("click", (e) => {
    if (e.target === editModal) editModal.classList.remove("open");
  });
}

function setSelectValue(selectId, value) {
  const select = document.getElementById(selectId);
  if (!select) return;
  for (const option of select.options) {
    if (option.value === value) {
      option.selected = true;
      break;
    }
  }
}

// ── Quantity +/- buttons in Edit modal ──
const editQtyInput = document.getElementById("edit-quantity");
const editQtyMinus = document.getElementById("edit-qty-minus");
const editQtyPlus = document.getElementById("edit-qty-plus");

if (editQtyMinus && editQtyInput) {
  editQtyMinus.addEventListener("click", () => {
    const val = parseFloat(editQtyInput.value) || 1;
    if (val > 1) editQtyInput.value = Math.round((val - 1) * 100) / 100;
  });
}

if (editQtyPlus && editQtyInput) {
  editQtyPlus.addEventListener("click", () => {
    const val = parseFloat(editQtyInput.value) || 0;
    editQtyInput.value = Math.round((val + 1) * 100) / 100;
  });
}

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

// ── Card quantity +/- buttons ──
// ── Card quantity +/- buttons ──
document.querySelectorAll(".card-qty-btn").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const id = btn.dataset.id;
    const action = btn.dataset.action;

    // ถ้า quantity = 1 และกด decrease → ถามก่อนลบ
    if (action === "decrease") {
      const display = document.getElementById(`qty-display-${id}`);
      const currentQty = parseFloat(display.textContent.trim());
      if (currentQty <= 1) {
        const confirmed = confirm(
          "This ingredient is out of stock. Do you want to remove it?",
        );
        if (!confirmed) return;

        // ลบ ingredient ออกจาก DB
        await fetch(`/ingredient/${id}/delete`, { method: "POST" });
        // ลบการ์ดออกจาก UI
        const card = btn.closest(".ingredient-card");
        if (card) card.remove();
        return;
      }
    }

    const res = await fetch(`/ingredient/${id}/quantity`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action }),
    });

    if (res.ok) {
      const data = await res.json();
      const display = document.getElementById(`qty-display-${id}`);
      const unit = display.textContent.trim().replace(/^[\d.]+\s*/, "");
      display.textContent = `${data.quantity} ${unit}`;
    }
  });
});
