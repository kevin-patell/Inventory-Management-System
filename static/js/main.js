/**
 * Apex Global Inventory - Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function () {
  // 1. Sidebar Toggle for Mobile & Compact views
  const menuToggle = document.getElementById('menu-toggle');
  const sidebar = document.getElementById('sidebar-wrapper');
  const content = document.getElementById('page-content-wrapper');

  if (menuToggle && sidebar && content) {
    menuToggle.addEventListener('click', function (e) {
      e.preventDefault();
      sidebar.classList.toggle('toggled');
      content.classList.toggle('toggled');
    });
  }

  // 2. Initialize Bootstrap Tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // 3. Auto-hide Flash Messages after 6 seconds
  setTimeout(function () {
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    });
  }, 6000);

  // 4. Live Notification Poller
  const notifBadge = document.getElementById('notif-badge');
  const notifDropdownList = document.getElementById('notif-dropdown-list');

  function updateNotifications() {
    if (!notifBadge) return;
    fetch('/notifications/latest')
      .then(response => response.json())
      .then(data => {
        if (data.unread_count > 0) {
          notifBadge.textContent = data.unread_count;
          notifBadge.style.display = 'inline-block';
        } else {
          notifBadge.style.display = 'none';
        }

        if (notifDropdownList && data.notifications) {
          if (data.notifications.length === 0) {
            notifDropdownList.innerHTML = '<li class="p-3 text-center text-muted small">No notifications yet.</li>';
          } else {
            let html = '';
            data.notifications.forEach(n => {
              const unreadClass = !n.is_read ? 'bg-light font-weight-bold' : '';
              let icon = 'bi-bell text-primary';
              if (n.type === 'out_of_stock') icon = 'bi-exclamation-octagon-fill text-danger';
              else if (n.type === 'low_stock') icon = 'bi-exclamation-triangle-fill text-warning';
              else if (n.type === 'purchase') icon = 'bi-box-arrow-in-down text-info';
              else if (n.type === 'sale') icon = 'bi-cash-coin text-success';

              html += `
                <li>
                  <a class="dropdown-item py-2 px-3 border-bottom ${unreadClass}" href="${n.link || '/notifications'}">
                    <div class="d-flex align-items-center gap-2">
                      <i class="bi ${icon} fs-5"></i>
                      <div class="flex-grow-1 overflow-hidden">
                        <div class="text-truncate fw-semibold small">${n.title}</div>
                        <div class="text-truncate text-muted extra-small" style="font-size:0.75rem;">${n.message}</div>
                      </div>
                    </div>
                  </a>
                </li>
              `;
            });
            notifDropdownList.innerHTML = html;
          }
        }
      })
      .catch(err => console.log('Notification poll error:', err));
  }

  // Poll notifications every 30 seconds
  if (notifBadge) {
    updateNotifications();
    setInterval(updateNotifications, 30000);
  }
});
