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

  // ── Delete Ingredient (from Edit Modal) ──
  const deleteBtn = document.getElementById("edit-delete-btn");
  const deleteForm = document.getElementById("delete-form");

  if (deleteBtn && deleteForm) {
    deleteBtn.addEventListener("click", () => {
      const confirmed = confirm(
        "Are you sure you want to delete this ingredient?",
      );
      if (!confirmed) return;
      deleteForm.action = editForm.action.replace("/edit", "/delete");
      deleteForm.submit();
    });
  }
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

function getEditStep() {
  const unit = document.getElementById("edit-unit").value.trim();
  return ["g", "ml", "l"].includes(unit) ? 5 : 1;
}

if (editQtyMinus && editQtyInput) {
  editQtyMinus.addEventListener("click", () => {
    const val = parseFloat(editQtyInput.value) || 1;
    const step = getEditStep();
    if (val > step) editQtyInput.value = Math.round((val - step) * 100) / 100;
  });
}

if (editQtyPlus && editQtyInput) {
  editQtyPlus.addEventListener("click", () => {
    const val = parseFloat(editQtyInput.value) || 0;
    const step = getEditStep();
    editQtyInput.value = Math.round((val + step) * 100) / 100;
  });
}

// ── Click on card to open edit modal ──
document.querySelectorAll(".ingredient-card").forEach((card) => {
  card.addEventListener("click", (e) => {
    if (e.target.closest(".btn-edit-ingredient")) return;

    const btn = card.querySelector(".btn-edit-ingredient");
    if (btn) btn.click();
  });
});

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

// ── Sort ingredients ──
const sortBtn = document.getElementById("sort-btn");
const sortDropdown = document.getElementById("sort-dropdown");

if (sortBtn && sortDropdown) {
  // Toggle dropdown open/close
  sortBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    const isOpen = sortDropdown.style.display === "flex";
    sortDropdown.style.display = isOpen ? "none" : "flex";
  });

  // Close dropdown when clicking outside
  document.addEventListener("click", () => {
    sortDropdown.style.display = "none";
  });

  // Prevent clicks inside dropdown from closing it
  sortDropdown.addEventListener("click", (e) => {
    e.stopPropagation();
  });

  sortDropdown.querySelectorAll(".sort-option").forEach((option) => {
    option.addEventListener("click", () => {
      // Update active state
      sortDropdown
        .querySelectorAll(".sort-option")
        .forEach((o) => o.classList.remove("active"));
      option.classList.add("active");

      const sortBy = option.dataset.sort;
      const grid = document.getElementById("ingredient-grid");
      if (!grid) return;

      const cards = [...grid.querySelectorAll(".ingredient-card")];

      cards.sort((a, b) => {
        if (sortBy === "name") {
          return (a.dataset.name || "").localeCompare(b.dataset.name || "");
        }
        if (sortBy === "expiry-asc") {
          const da = a.dataset.expiry || "9999-12-31";
          const db = b.dataset.expiry || "9999-12-31";
          return da.localeCompare(db);
        }
        if (sortBy === "expiry-desc") {
          const da = a.dataset.expiry || "0000-01-01";
          const db = b.dataset.expiry || "0000-01-01";
          return db.localeCompare(da);
        }
        if (sortBy === "date-added-asc") {
          return parseInt(a.dataset.id) - parseInt(b.dataset.id);
        }
        // date-added-desc (default)
        return parseInt(b.dataset.id) - parseInt(a.dataset.id);
      });

      cards.forEach((card) => grid.appendChild(card));
      sortDropdown.style.display = "none";
    });
  });
}

// ── Filter tabs — show/hide ingredient cards by category ──
const filterTabs = document.querySelectorAll(".filter-tab");
const ingredientCards = document.querySelectorAll(".ingredient-card");

filterTabs.forEach((tab) => {
  tab.addEventListener("click", () => {
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
    let visibleCount = 0;

    ingredientCards.forEach((card) => {
      const name = card.dataset.name || "";
      const visible = name.includes(query);
      card.style.display = visible ? "" : "none";
      if (visible) visibleCount++;
    });

    const emptyMsg = document.getElementById("no-results-msg");
    if (emptyMsg)
      emptyMsg.style.display = visibleCount === 0 ? "block" : "none";
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
