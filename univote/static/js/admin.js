/* ─── Univote Admin JavaScript ─────────────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', function () {

  // ─── Sidebar Toggle ──────────────────────────────────────────────────────
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');
  const mainContent = document.getElementById('main-content');

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', function () {
      sidebar.classList.toggle('open');
    });

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function (e) {
      if (window.innerWidth <= 992) {
        if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
          sidebar.classList.remove('open');
        }
      }
    });
  }

  // ─── Auto-dismiss alerts after 4 seconds ─────────────────────────────────
  document.querySelectorAll('.alert.alert-dismissible').forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 4000);
  });

  // ─── Confirm delete forms ─────────────────────────────────────────────────
  document.querySelectorAll('form[data-confirm]').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      const msg = this.dataset.confirm || 'Are you sure?';
      if (!confirm(msg)) e.preventDefault();
    });
  });

  // ─── Copy voting link buttons ─────────────────────────────────────────────
  document.querySelectorAll('.copy-link-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const link = this.dataset.link;
      if (!link) return;
      navigator.clipboard.writeText(link).then(function () {
        showToast('Voting link copied to clipboard!', 'success');
      }).catch(function () {
        // Fallback
        const input = document.createElement('input');
        input.value = link;
        document.body.appendChild(input);
        input.select();
        document.execCommand('copy');
        document.body.removeChild(input);
        showToast('Link copied!', 'success');
      });
    });
  });

  // ─── Global toast function ─────────────────────────────────────────────────
  window.showToast = function (message, type = 'info') {
    const existing = document.querySelectorAll('.toast-notification');
    existing.forEach(t => t.remove());

    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 2700);
  };

  // ─── Table row hover highlight ────────────────────────────────────────────
  document.querySelectorAll('.table-hover tbody tr').forEach(function (row) {
    row.style.cursor = 'default';
  });

  // ─── Date/time input helpers ──────────────────────────────────────────────
  const dateInputs = document.querySelectorAll('input[type="datetime-local"]');
  if (dateInputs.length > 0) {
    const now = new Date();
    const pad = n => String(n).padStart(2, '0');
    const localNow = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}T${pad(now.getHours())}:${pad(now.getMinutes())}`;
    dateInputs.forEach(input => {
      if (!input.value && !input.min) {
        input.min = localNow;
      }
    });
  }

  // ─── Theme Toggle ─────────────────────────────────────────────────────────
  const themeToggle = document.getElementById('themeToggle');
  const themeIcon = document.getElementById('themeIcon');
  
  if (themeToggle) {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    updateThemeIcon(currentTheme);

    themeToggle.addEventListener('click', function() {
      const activeTheme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', activeTheme);
      localStorage.setItem('theme', activeTheme);
      updateThemeIcon(activeTheme);
    });
  }

  function updateThemeIcon(theme) {
    if (!themeIcon) return;
    if (theme === 'dark') {
      themeIcon.className = 'bi bi-sun-fill';
      themeToggle.title = 'Switch to Light Mode';
    } else {
      themeIcon.className = 'bi bi-moon-fill';
      themeToggle.title = 'Switch to Dark Mode';
    }
  }

});
