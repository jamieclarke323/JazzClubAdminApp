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

// Idea list pages: clicking a row (but not its delete button) toggles the full-detail row below it.
document.addEventListener('click', function (event) {
  if (event.target.closest('form') || event.target.closest('a')) return;
  var row = event.target.closest('[data-idea-toggle]');
  if (!row) return;
  var target = document.getElementById(row.getAttribute('data-target'));
  if (target) target.hidden = !target.hidden;
});

// Category manager: add/rename/delete without a full page reload.
function escapeHtml(value) {
  var div = document.createElement('div');
  div.textContent = value;
  return div.innerHTML;
}

document.addEventListener('submit', function (event) {
  var form = event.target.closest('[data-category-form]');
  if (!form) return;
  event.preventDefault();

  var manager = form.closest('.category-manager');
  var kind = manager ? manager.getAttribute('data-kind') : '';
  var list = manager ? manager.querySelector('[data-category-list]') : null;
  var countEl = manager ? manager.querySelector('[data-category-count]') : null;
  var categoryId = form.getAttribute('data-category-id');

  var action;
  if (form.classList.contains('category-create-form')) {
    action = '/ideas/' + kind + '/categories/create/';
  } else if (form.classList.contains('category-rename-form')) {
    action = '/ideas/' + kind + '/categories/' + categoryId + '/update/';
  } else {
    action = '/ideas/' + kind + '/categories/' + categoryId + '/delete/';
  }

  fetch(action, {
    method: 'POST',
    headers: { 'X-Requested-With': 'XMLHttpRequest' },
    body: new FormData(form),
  })
    .then(function (response) { return response.json(); })
    .then(function (data) {
      if (!data.success) return;

      if (form.classList.contains('category-create-form')) {
        var emptyRow = list.querySelector('[data-category-empty]');
        if (emptyRow) emptyRow.remove();

        var csrfToken = form.querySelector('input[name="csrfmiddlewaretoken"]').value;
        var li = document.createElement('li');
        li.className = 'category-manage-row';
        li.setAttribute('data-category-row', '');
        li.setAttribute('data-category-id', data.id);
        li.innerHTML =
          '<form class="category-rename-form" data-category-form data-category-id="' + data.id + '">' +
            '<input type="hidden" name="csrfmiddlewaretoken" value="' + escapeHtml(csrfToken) + '">' +
            '<input type="text" name="name" value="' + escapeHtml(data.name) + '">' +
            '<button type="submit" class="ghost-button small">Save</button>' +
          '</form>' +
          '<form class="category-delete-form" data-category-form data-category-id="' + data.id + '">' +
            '<input type="hidden" name="csrfmiddlewaretoken" value="' + escapeHtml(csrfToken) + '">' +
            '<button type="submit" class="icon-button" aria-label="Delete category">×</button>' +
          '</form>';
        list.appendChild(li);
        form.reset();
      } else if (form.classList.contains('category-delete-form')) {
        var row = form.closest('[data-category-row]');
        if (row) row.remove();
        if (list && !list.querySelector('[data-category-row]')) {
          var empty = document.createElement('li');
          empty.className = 'muted';
          empty.setAttribute('data-category-empty', '');
          empty.textContent = 'No categories yet.';
          list.appendChild(empty);
        }
      }

      if (countEl && list) {
        var count = list.querySelectorAll('[data-category-row]').length;
        countEl.textContent = count + (count === 1 ? ' category' : ' categories');
      }
    });
});

