/**
 * home.js
 * -------
 * Home Interior Planner — form interactivity
 *
 * Responsibilities:
 *  1. Show/hide per-room item panels when room checkboxes are toggled
 *  2. Add / remove item rows within each room panel
 *  3. Quick-add suggestion chips
 *  4. Sync visible item data into hidden <input> fields before submit
 *  5. Client-side validation (at least one room selected, budget > 0)
 *  6. Show loading overlay on valid submit
 */

(function () {
  'use strict';

  // ── Room checkbox handling ─────────────────────────────────────
  const roomCheckboxes = document.querySelectorAll('.room-checkbox');

  roomCheckboxes.forEach(function (cb) {
    cb.addEventListener('change', function () {
      const room     = this.dataset.room;
      const panel    = document.getElementById('items_' + room);
      const tile     = this.closest('.room-tile');

      if (this.checked) {
        tile.classList.add('selected');
        panel.style.display = 'block';
        // Add one starter row if the panel is empty
        if (getItemRows(room).length === 0) {
          addItemRow(room);
        }
      } else {
        tile.classList.remove('selected');
        panel.style.display = 'none';
      }
    });
  });

  // ── Item row management ────────────────────────────────────────
  function getItemRows(room) {
    return document.querySelectorAll('#rows_' + room + ' .item-row');
  }

  function addItemRow(room, itemName) {
    const container = document.getElementById('rows_' + room);
    const idx       = container.querySelectorAll('.item-row').length;

    const row       = document.createElement('div');
    row.className   = 'item-row';
    row.dataset.room = room;

    row.innerHTML =
      '<input type="text" placeholder="Item name e.g. Sofa" value="' +
        escapeAttr(itemName || '') + '" data-role="item-name" />' +
      '<input type="number" min="1" max="99" value="1" data-role="item-qty" ' +
        'title="Quantity" aria-label="Quantity" />' +
      '<button type="button" class="remove-item-btn" title="Remove" aria-label="Remove item">' +
        '✕</button>';

    row.querySelector('.remove-item-btn').addEventListener('click', function () {
      row.remove();
    });

    container.appendChild(row);
  }

  // ── Suggestion chips ───────────────────────────────────────────
  document.querySelectorAll('.suggestion-chip').forEach(function (chip) {
    chip.addEventListener('click', function () {
      const room = this.dataset.room;
      const item = this.dataset.item;
      addItemRow(room, item);
    });
  });

  // ── Build hidden inputs before submit ─────────────────────────
  function syncHiddenInputs() {
    // Clear all existing hidden inputs
    document.querySelectorAll('.hidden-inputs').forEach(function (div) {
      div.innerHTML = '';
    });

    roomCheckboxes.forEach(function (cb) {
      if (!cb.checked) return;
      const room        = cb.dataset.room;
      const hiddenDiv   = document.getElementById('hidden_' + room);
      const rows        = document.querySelectorAll('#rows_' + room + ' .item-row');

      rows.forEach(function (row) {
        const nameInput = row.querySelector('[data-role="item-name"]');
        const qtyInput  = row.querySelector('[data-role="item-qty"]');
        const name      = (nameInput ? nameInput.value.trim() : '');
        const qty       = (qtyInput  ? qtyInput.value  : '1');

        if (!name) return; // skip blank rows

        const nameField  = document.createElement('input');
        nameField.type   = 'hidden';
        nameField.name   = room + '_items[]';
        nameField.value  = name;

        const qtyField   = document.createElement('input');
        qtyField.type    = 'hidden';
        qtyField.name    = room + '_quantities[]';
        qtyField.value   = qty;

        hiddenDiv.appendChild(nameField);
        hiddenDiv.appendChild(qtyField);
      });
    });
  }

  // ── Form validation & submit ───────────────────────────────────
  const form       = document.getElementById('homePlannerForm');
  const roomError  = document.getElementById('roomError');
  const budgetInput = document.getElementById('budget');

  if (form) {
    form.addEventListener('submit', function (e) {
      let valid = true;

      // Validate budget
      const budget = parseFloat(budgetInput ? budgetInput.value : '0');
      if (!budget || budget <= 0) {
        budgetInput && budgetInput.focus();
        valid = false;
      }

      // Validate at least one room selected
      const anyChecked = Array.from(roomCheckboxes).some(function (cb) { return cb.checked; });
      if (!anyChecked) {
        roomError && (roomError.style.display = 'block');
        valid = false;
      } else {
        roomError && (roomError.style.display = 'none');
      }

      if (!valid) {
        e.preventDefault();
        return;
      }

      // Sync hidden inputs then show loading
      syncHiddenInputs();
      if (window.showLoading) window.showLoading();
    });
  }

  // ── Utility ───────────────────────────────────────────────────
  function escapeAttr(str) {
    return str.replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

})();
