/* ─── Univote Voting Page JavaScript ──────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', function () {

  // ─── OTP Auto-submit on 6 digits ─────────────────────────────────────────
  const otpInput = document.getElementById('otp');
  if (otpInput) {
    otpInput.addEventListener('input', function () {
      this.value = this.value.replace(/[^0-9]/g, '').slice(0, 6);
    });
    otpInput.focus();
  }

  // ─── Checkbox max selection enforcement ──────────────────────────────────
  document.querySelectorAll('.candidate-checkbox').forEach(function (cb) {
    cb.addEventListener('change', function () {
      const posId = this.dataset.position;
      const max = parseInt(this.dataset.max, 10);
      if (isNaN(max)) return;

      // If abstain is checked, uncheck all others and vice versa
      if (this.classList.contains('abstain-check') && this.checked) {
        document.querySelectorAll(
          `.candidate-checkbox[data-position="${posId}"]:not(.abstain-check)`
        ).forEach(c => {
          c.checked = false;
          c.closest('.candidate-card-label')?.classList.remove('selected');
        });
      } else if (!this.classList.contains('abstain-check') && this.checked) {
        document.querySelectorAll(
          `.abstain-check[data-position="${posId}"]`
        ).forEach(c => {
          c.checked = false;
          c.closest('.candidate-card-label')?.classList.remove('selected');
        });
      }

      const allChecked = document.querySelectorAll(
        `.candidate-checkbox[data-position="${posId}"]:checked`
      );
      const feedback = document.getElementById(`feedback_${posId}`);

      if (allChecked.length > max) {
        this.checked = false;
        this.closest('.candidate-card-label')?.classList.remove('selected');
        if (feedback) {
          feedback.textContent = `⚠️ You can only select up to ${max} candidate(s) for this position.`;
          feedback.className = 'selection-feedback selection-error';
        }
        return;
      }

      if (feedback) {
        if (allChecked.length > 0) {
          feedback.textContent = `✓ ${allChecked.length} of ${max} selected.`;
          feedback.className = 'selection-feedback selection-ok';
        } else {
          feedback.textContent = '';
        }
      }
    });
  });

  // ─── Visual card selection state (radio + checkbox) ──────────────────────
  document.querySelectorAll('.candidate-card-label').forEach(function (label) {
    const input = label.querySelector('input');
    if (!input) return;

    input.addEventListener('change', function () {
      if (this.type === 'radio') {
        // Deselect siblings in same group
        document.querySelectorAll(`input[name="${this.name}"]`).forEach(r => {
          r.closest('.candidate-card-label')?.classList.remove('selected');
        });
        if (this.checked) {
          label.classList.add('selected');
        }
      } else {
        if (this.checked) {
          label.classList.add('selected');
        } else {
          label.classList.remove('selected');
        }
      }
    });
  });

  // ─── Prevent double-submit on forms ──────────────────────────────────────
  document.querySelectorAll('form').forEach(function (form) {
    let submitted = false;
    form.addEventListener('submit', function (e) {
      if (submitted) {
        e.preventDefault();
        return false;
      }
      submitted = true;
      // Reset after 10s in case of server error
      setTimeout(() => { submitted = false; }, 10000);
    });
  });

  // ─── Smooth scroll for step indicator ────────────────────────────────────
  const positionBlocks = document.querySelectorAll('.position-block');
  if (positionBlocks.length > 0) {
    const observer = new IntersectionObserver(function (entries) {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.style.opacity = '1';
          entry.target.style.transform = 'translateY(0)';
        }
      });
    }, { threshold: 0.1 });

    positionBlocks.forEach(block => {
      block.style.opacity = '0';
      block.style.transform = 'translateY(10px)';
      block.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      observer.observe(block);
    });
  }

  // ─── Receipt auto-print option ────────────────────────────────────────────
  const receiptCard = document.querySelector('.receipt-card');
  if (receiptCard) {
    // Animate receipt on load
    receiptCard.style.opacity = '0';
    receiptCard.style.transform = 'scale(0.95)';
    receiptCard.style.transition = 'all 0.4s ease';
    setTimeout(() => {
      receiptCard.style.opacity = '1';
      receiptCard.style.transform = 'scale(1)';
    }, 200);
  }
});
