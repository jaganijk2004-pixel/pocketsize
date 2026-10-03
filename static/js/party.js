/**
 * party.js
 * --------
 * Party Budget Planner — form interactivity
 *
 * Responsibilities:
 *  1. Character counter for special requirements textarea
 *  2. Client-side validation (budget > 0, guests > 0, event type selected)
 *  3. Show loading overlay on valid submit
 */

(function () {
  'use strict';

  // ── Character counter ──────────────────────────────────────────
  const reqTextarea  = document.getElementById('special_requirements');
  const reqCharCount = document.getElementById('reqCharCount');

  if (reqTextarea && reqCharCount) {
    reqTextarea.addEventListener('input', function () {
      const len = this.value.length;
      const max = parseInt(this.getAttribute('maxlength') || '500', 10);
      reqCharCount.textContent = len + ' / ' + max;
      reqCharCount.style.color = len > max * 0.9
        ? 'var(--color-warning)'
        : 'var(--color-text-muted)';
    });
  }

  // ── Form validation & submit ───────────────────────────────────
  const form        = document.getElementById('partyPlannerForm');
  const budgetInput = document.getElementById('budget');
  const guestsInput = document.getElementById('guests');
  const eventSelect = document.getElementById('event_type');

  if (form) {
    form.addEventListener('submit', function (e) {
      let valid   = true;
      let firstInvalid = null;

      // Validate budget
      const budget = parseFloat(budgetInput ? budgetInput.value : '0');
      if (!budget || budget <= 0) {
        markInvalid(budgetInput, 'Please enter a valid budget.');
        firstInvalid = firstInvalid || budgetInput;
        valid = false;
      } else {
        markValid(budgetInput);
      }

      // Validate guests
      const guests = parseInt(guestsInput ? guestsInput.value : '0', 10);
      if (!guests || guests <= 0) {
        markInvalid(guestsInput, 'Please enter the number of guests.');
        firstInvalid = firstInvalid || guestsInput;
        valid = false;
      } else {
        markValid(guestsInput);
      }

      // Validate event type
      if (eventSelect && !eventSelect.value) {
        markInvalid(eventSelect, 'Please select an event type.');
        firstInvalid = firstInvalid || eventSelect;
        valid = false;
      } else {
        markValid(eventSelect);
      }

      if (!valid) {
        e.preventDefault();
        if (firstInvalid) firstInvalid.focus();
        return;
      }

      if (window.showLoading) window.showLoading();
    });
  }

  // ── Inline validation helpers ──────────────────────────────────
  function markInvalid(el, message) {
    if (!el) return;
    el.style.borderColor = 'var(--color-error)';
    el.style.boxShadow   = '0 0 0 3px rgba(239,68,68,.15)';

    let hint = el.parentElement.querySelector('.inline-error');
    if (!hint) {
      hint           = document.createElement('p');
      hint.className = 'form-hint inline-error';
      hint.style.color = 'var(--color-error)';
      el.parentElement.appendChild(hint);
    }
    hint.textContent = message;
  }

  function markValid(el) {
    if (!el) return;
    el.style.borderColor = '';
    el.style.boxShadow   = '';
    const hint = el.parentElement.querySelector('.inline-error');
    if (hint) hint.remove();
  }

})();
