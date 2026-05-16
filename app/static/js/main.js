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

if (modalOverlay) {
  modalOverlay.addEventListener("click", (e) => {
    if (e.target === modalOverlay) closeModal();
  });
}

// ── Edit Ingredient Modal ──
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

      const lowStockToggle = document.getElementById("edit-is-low-stock");
      if (lowStockToggle) {
        lowStockToggle.checked = btn.dataset.isLowStock === "true";
      }

      editModal.classList.add("open");
    });
  });

  document.getElementById("edit-cancel-btn").addEventListener("click", () => {
    editModal.classList.remove("open");
  });

  editModal.addEventListener("click", (e) => {
    if (e.target === editModal) editModal.classList.remove("open");
  });

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
  return ["g", "ml"].includes(unit) ? 5 : 1;
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

// ── Quantity +/- buttons in Add modal ──
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
  sortBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    const isOpen = sortDropdown.style.display === "flex";
    sortDropdown.style.display = isOpen ? "none" : "flex";
  });

  document.addEventListener("click", () => {
    sortDropdown.style.display = "none";
  });

  sortDropdown.addEventListener("click", (e) => {
    e.stopPropagation();
  });

  sortDropdown.querySelectorAll(".sort-option").forEach((option) => {
    option.addEventListener("click", () => {
      sortDropdown
        .querySelectorAll(".sort-option")
        .forEach((o) => o.classList.remove("active"));
      option.classList.add("active");

      const sortBy = option.dataset.sort;
      const grid = document.getElementById("ingredient-grid");
      if (!grid) return;

      const cards = [...grid.querySelectorAll(".ingredient-card")];

      cards.sort((a, b) => {
        if (sortBy === "name-asc")
          return (a.dataset.name || "").localeCompare(b.dataset.name || "");
        if (sortBy === "name-dsc")
          return (b.dataset.name || "").localeCompare(a.dataset.name || "");
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
        if (sortBy === "date-added-asc")
          return parseInt(a.dataset.id) - parseInt(b.dataset.id);
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
      const visible = name.startsWith(query);
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

// ── Low stock — apply .amount-low class on page load ──
document
  .querySelectorAll(".ingredient-quantity[data-is-low-stock]")
  .forEach((span) => {
    if (span.dataset.isLowStock === "true") {
      span.classList.add("amount-low");
    }
  });

// ── Shopping list: quantity +/- controls ──
document.querySelectorAll(".sl-qty-ctrl").forEach((btn) => {
  btn.addEventListener("click", () => {
    const id = btn.dataset.id;
    const action = btn.dataset.action;
    fetch(`/shopping-list/quantity/${id}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action }),
    })
      .then((res) => res.json())
      .then((data) => {
        const valEl = document.getElementById(`sl-qty-${id}`);
        if (valEl) valEl.textContent = data.quantity;
      });
  });
});

// ── Shopping list: budget bar (US17) ──
function updateBudgetBar() {
  const card = document.querySelector(".sl-budget-card");
  if (!card) return;

  const budget = parseFloat(card.dataset.budget) || 0;
  const spentEl = document.querySelector(".sl-budget-spent");
  const spentText = spentEl ? spentEl.textContent.replace("spent €", "") : "0";
  const spent = parseFloat(spentText) || 0;

  const bar = document.getElementById("sl-budget-bar");
  const remainingEl = document.querySelector(".sl-budget-remaining");

  if (budget > 0) {
    const pct = Math.min((spent / budget) * 100, 100);
    if (bar) {
      bar.style.width = `${pct}%`;
      bar.className = "sl-budget-bar";
      if (pct >= 100) bar.classList.add("danger");
      else if (pct >= 75) bar.classList.add("warning");
    }
  } else {
    if (bar) bar.style.width = "0%";
  }

  if (remainingEl) {
    const remaining = budget - spent;
    remainingEl.textContent = `€${remaining.toFixed(2)}`;
    if (remaining < 0) remainingEl.classList.add("over-budget");
    else remainingEl.classList.remove("over-budget");
  }
}

updateBudgetBar();

// ── Shopping list: toggle check with price modal ──
let pendingToggleBtn = null;
const slPriceOverlay = document.getElementById("sl-price-overlay");
const slPriceField = document.getElementById("sl-price-field");
const slPriceSave = document.getElementById("sl-price-save");
const slPriceCancel = document.getElementById("sl-price-cancel");

function doToggle(btn, price = "") {
  const id = btn.dataset.id;
  fetch(`/shopping-list/toggle/${id}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ price }),
  })
    .then((res) => res.json())
    .then((data) => {
      // อัปเดต spent
      const spentEl = document.querySelector(".sl-budget-spent");
      if (spentEl && data.total_spent !== undefined) {
        spentEl.textContent = `spent €${data.total_spent.toFixed(2)}`;
      }

      const item = btn.closest(".sl-item");
      const priceEl = item.querySelector(".sl-item-price");

      if (data.is_checked) {
        btn.classList.add("sl-check--checked");
        btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14"
          viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"
          stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>`;
        item.classList.add("sl-item--done");
        item.dataset.filter = "done";

        if (price && parseFloat(price) > 0) {
          const nameEl = item.querySelector(".sl-item-name");
          if (!priceEl) {
            const span = document.createElement("span");
            span.className = "sl-item-price";
            span.textContent = `€${parseFloat(price).toFixed(2)}`;
            nameEl.after(span);
          } else {
            priceEl.textContent = `€${parseFloat(price).toFixed(2)}`;
          }
        }
      } else {
        btn.classList.remove("sl-check--checked");
        btn.innerHTML = "";
        item.classList.remove("sl-item--done");
        item.dataset.filter = "tobuy";
        if (priceEl) priceEl.remove();
      }

      updateShoppingProgress();
      updateBudgetBar();
    });
}

// Price overlay — close on background click (registered once)
if (slPriceOverlay) {
  slPriceOverlay.addEventListener("click", (e) => {
    if (e.target === slPriceOverlay) {
      slPriceOverlay.classList.remove("open");
      pendingToggleBtn = null;
    }
  });
}

// Checkbox click
document.querySelectorAll(".sl-check").forEach((btn) => {
  btn.addEventListener("click", () => {
    const item = btn.closest(".sl-item");
    if (item.classList.contains("sl-item--done")) return;

    pendingToggleBtn = btn;
    if (slPriceField) slPriceField.value = "";
    const itemName = item.querySelector(".sl-item-name").textContent;
    const msgEl = document.getElementById("sl-price-msg");
    if (msgEl)
      msgEl.textContent = `How much did you pay for ${itemName}? (optional)`;
    if (slPriceOverlay) slPriceOverlay.classList.add("open");
    setTimeout(() => slPriceField && slPriceField.focus(), 100);
  });
});

if (slPriceSave) {
  slPriceSave.addEventListener("click", () => {
    const price = slPriceField ? slPriceField.value : "";
    slPriceOverlay.classList.remove("open");
    if (pendingToggleBtn) doToggle(pendingToggleBtn, price);
    pendingToggleBtn = null;
  });
}

if (slPriceCancel) {
  slPriceCancel.addEventListener("click", () => {
    slPriceOverlay.classList.remove("open");
    pendingToggleBtn = null;
  });
}

if (slPriceField) {
  slPriceField.addEventListener("keydown", (e) => {
    if (e.key === "Enter") slPriceSave && slPriceSave.click();
  });
}

// ── Shopping list: progress update ──
function updateShoppingProgress() {
  const allItems = document.querySelectorAll(".sl-item");
  const total = allItems.length;
  const checked = document.querySelectorAll(".sl-item.sl-item--done").length;
  const toBuy = total - checked;
  const pct = total > 0 ? Math.round((checked / total) * 100) : 0;

  const numEl = document.querySelector(".sl-progress-num");
  const totalEl = document.querySelector(".sl-progress-total");
  const hintEl = document.querySelector(".sl-progress-hint");
  const barEl = document.querySelector(".sl-progress-bar");
  const pctEl = document.querySelector(".sl-progress-pct");

  if (numEl) numEl.childNodes[0].textContent = checked;
  if (totalEl) totalEl.textContent = `/${total}`;
  if (hintEl)
    hintEl.textContent = `${toBuy} item${toBuy !== 1 ? "s" : ""} to go ↗`;
  if (barEl) barEl.style.width = `${pct}%`;
  if (pctEl) pctEl.textContent = `${pct}%`;

  document.querySelectorAll(".sl-tab").forEach((tab) => {
    if (tab.dataset.filter === "all") tab.textContent = `All · ${total}`;
    if (tab.dataset.filter === "tobuy") tab.textContent = `To buy · ${toBuy}`;
    if (tab.dataset.filter === "done") tab.textContent = `Done · ${checked}`;
  });

  const clearBtn = document.querySelector(".sl-clear-btn");
  if (clearBtn) {
    if (checked > 0) clearBtn.classList.remove("sl-clear-disabled");
    else clearBtn.classList.add("sl-clear-disabled");
  }
}

// ── Shopping list: delete with custom modal ──
let pendingDeleteForm = null;
const slConfirmOverlay = document.getElementById("sl-confirm-overlay");
const slConfirmOk = document.getElementById("sl-confirm-ok");
const slConfirmCancel = document.getElementById("sl-confirm-cancel");

document.querySelectorAll(".sl-item-delete-form").forEach((form) => {
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    pendingDeleteForm = form;
    if (slConfirmOverlay) slConfirmOverlay.classList.add("open");
  });
});

if (slConfirmOk) {
  slConfirmOk.addEventListener("click", () => {
    if (pendingDeleteForm) pendingDeleteForm.submit();
    slConfirmOverlay.classList.remove("open");
  });
}

if (slConfirmCancel) {
  slConfirmCancel.addEventListener("click", () => {
    pendingDeleteForm = null;
    slConfirmOverlay.classList.remove("open");
  });
}

// ── Shopping list: filter tabs ──
const slTabs = document.querySelectorAll(".sl-tab");
const slItems = document.querySelectorAll(".sl-item");

slTabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    slTabs.forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    const filter = tab.dataset.filter;
    slItems.forEach((item) => {
      if (filter === "all" || item.dataset.filter === filter) {
        item.classList.remove("sl-item--hidden");
      } else {
        item.classList.add("sl-item--hidden");
      }
    });
  });
});
