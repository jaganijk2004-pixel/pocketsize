/**
 * jewelry.js
 * ----------
 * Jewelry Budget Planner — form interactivity
 *
 * Responsibilities:
 *  1. Image file preview on file input change
 *  2. Drag-and-drop onto the upload zone
 *  3. File type and size validation (max 5 MB, allowed types)
 *  4. Remove image button
 *  5. Client-side validation (budget > 0, occasion selected, style selected)
 *  6. Show loading overlay on valid submit
 */

(function () {
  'use strict';

  const MAX_FILE_SIZE   = 5 * 1024 * 1024; // 5 MB
  const ALLOWED_TYPES   = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
  const ALLOWED_EXT_RE  = /\.(jpg|jpeg|png|webp)$/i;

  // ── DOM refs ───────────────────────────────────────────────────
  const uploadZone       = document.getElementById('uploadZone');
  const fileInput        = document.getElementById('outfit_image');
  const uploadPlaceholder = document.getElementById('uploadPlaceholder');
  const uploadPreview    = document.getElementById('uploadPreview');
  const previewImg       = document.getElementById('previewImg');
  const previewFilename  = document.getElementById('previewFilename');
  const previewFilesize  = document.getElementById('previewFilesize');
  const removeBtn        = document.getElementById('removeImage');
  const uploadError      = document.getElementById('uploadError');

  // ── Image preview ──────────────────────────────────────────────
  function handleFile(file) {
    if (!file) return;

    // Validate type
    const ext = '.' + file.name.split('.').pop();
    if (!ALLOWED_TYPES.includes(file.type) && !ALLOWED_EXT_RE.test(file.name)) {
      showUploadError('Unsupported file type. Please upload a JPG, PNG, or WebP image.');
      clearFile();
      return;
    }

    // Validate size
    if (file.size > MAX_FILE_SIZE) {
      showUploadError('Image is too large. Maximum size is 5 MB.');
      clearFile();
      return;
    }

    hideUploadError();

    const reader = new FileReader();
    reader.onload = function (e) {
      previewImg.src       = e.target.result;
      previewFilename.textContent = file.name;
      previewFilesize.textContent = formatBytes(file.size);
      uploadPlaceholder.style.display = 'none';
      uploadPreview.style.display     = 'flex';
    };
    reader.readAsDataURL(file);
  }

  if (fileInput) {
    fileInput.addEventListener('change', function () {
      if (this.files && this.files[0]) {
        handleFile(this.files[0]);
      }
    });
  }

  // ── Remove image ───────────────────────────────────────────────
  if (removeBtn) {
    removeBtn.addEventListener('click', function (e) {
      e.preventDefault();
      clearFile();
    });
  }

  function clearFile() {
    if (fileInput) fileInput.value = '';
    if (previewImg) previewImg.src = '';
    if (previewFilename) previewFilename.textContent = '';
    if (previewFilesize) previewFilesize.textContent = '';
    if (uploadPlaceholder) uploadPlaceholder.style.display = 'block';
    if (uploadPreview)     uploadPreview.style.display     = 'none';
  }

  // ── Drag and drop ──────────────────────────────────────────────
  if (uploadZone) {
    uploadZone.addEventListener('dragover', function (e) {
      e.preventDefault();
      this.classList.add('dragover');
    });
    uploadZone.addEventListener('dragleave', function () {
      this.classList.remove('dragover');
    });
    uploadZone.addEventListener('drop', function (e) {
      e.preventDefault();
      this.classList.remove('dragover');
      const files = e.dataTransfer && e.dataTransfer.files;
      if (files && files[0]) {
        // Assign to input for form submission
        try {
          const dt = new DataTransfer();
          dt.items.add(files[0]);
          fileInput.files = dt.files;
        } catch (_) { /* DataTransfer not supported in all browsers */ }
        handleFile(files[0]);
      }
    });

    // Keyboard accessibility for upload zone
    uploadZone.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        fileInput && fileInput.click();
      }
    });
  }

  // ── Upload error helpers ───────────────────────────────────────
  function showUploadError(msg) {
    if (!uploadError) return;
    uploadError.textContent = msg;
    uploadError.style.display = 'block';
  }
  function hideUploadError() {
    if (!uploadError) return;
    uploadError.textContent = '';
    uploadError.style.display = 'none';
  }

  // ── Form validation & submit ───────────────────────────────────
  const form          = document.getElementById('jewelryPlannerForm');
  const budgetInput   = document.getElementById('budget');
  const occasionSelect = document.getElementById('occasion');
  const styleSelect   = document.getElementById('style');

  if (form) {
    form.addEventListener('submit', function (e) {
      let valid = true;
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

      // Validate occasion
      if (occasionSelect && !occasionSelect.value) {
        markInvalid(occasionSelect, 'Please select an occasion.');
        firstInvalid = firstInvalid || occasionSelect;
        valid = false;
      } else {
        markValid(occasionSelect);
      }

      // Validate style
      if (styleSelect && !styleSelect.value) {
        markInvalid(styleSelect, 'Please select a style preference.');
        firstInvalid = firstInvalid || styleSelect;
        valid = false;
      } else {
        markValid(styleSelect);
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

  // ── Utility ───────────────────────────────────────────────────
  function formatBytes(bytes) {
    if (bytes < 1024)       return bytes + ' B';
    if (bytes < 1048576)    return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  }

})();
