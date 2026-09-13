// Owner button groups support an unselected ("no owner") state, unlike native radios.
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
