// Owner picker buttons support an unselected ("no owner") state, unlike native radios.
document.addEventListener('click', function (event) {
  var button = event.target.closest('[data-toggle-value]');
  if (!button) return;

  var group = button.closest('[data-toggle-group]');
  if (!group) return;

  var hiddenInput = group.querySelector('input[type="hidden"]');
  var wasSelected = button.classList.contains('selected');

  group.querySelectorAll('[data-toggle-value]').forEach(function (option) {
    option.classList.remove('selected');
  });

  if (wasSelected) {
    hiddenInput.value = '';
  } else {
    button.classList.add('selected');
    hiddenInput.value = button.getAttribute('data-toggle-value');
  }
});

// Mobile hamburger menu: opens the sidebar as an off-canvas drawer that stays reachable while scrolling.
(function () {
  var toggle = document.getElementById('navToggle');
  var backdrop = document.getElementById('navBackdrop');
  var nav = document.getElementById('mobileNav');
  if (!toggle || !backdrop || !nav) return;

  function closeNav() {
    document.body.classList.remove('nav-open');
    toggle.setAttribute('aria-expanded', 'false');
  }

  function openNav() {
    document.body.classList.add('nav-open');
    toggle.setAttribute('aria-expanded', 'true');
  }

  toggle.addEventListener('click', function () {
    if (document.body.classList.contains('nav-open')) {
      closeNav();
    } else {
      openNav();
    }
  });

  backdrop.addEventListener('click', closeNav);
  nav.querySelectorAll('.nav-link').forEach(function (link) {
    link.addEventListener('click', closeNav);
  });
})();

// Only one task dropdown (⋯ options or ÷ sub-tasks) may be open per row at a time.
// The "toggle" event doesn't bubble, so listen during the capture phase instead.
document.addEventListener('toggle', function (event) {
  var details = event.target;
  if (!details.classList || !details.classList.contains('task-options') || !details.open) return;

  var row = details.closest('.task-row-actions');
  if (!row) return;

  row.querySelectorAll('.task-options').forEach(function (other) {
    if (other !== details && other.open) {
      other.open = false;
    }
  });
}, true);

// Today page: clicking a claimed task's card opens a popup to switch its owner.
document.addEventListener('click', function (event) {
  var trigger = event.target.closest('[data-owner-trigger]');
  if (trigger) {
    var row = trigger.closest('[data-owner-switch]');
    var panel = row && row.querySelector('[data-owner-panel]');
    if (!panel) return;
    var wasHidden = panel.hasAttribute('hidden');
    document.querySelectorAll('[data-owner-panel]').forEach(function (other) {
      other.setAttribute('hidden', '');
    });
    if (wasHidden) panel.removeAttribute('hidden');
    return;
  }
  if (!event.target.closest('[data-owner-panel]')) {
    document.querySelectorAll('[data-owner-panel]').forEach(function (panel) {
      panel.setAttribute('hidden', '');
    });
  }
});

