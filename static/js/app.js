(function () {
  const deleteModal = document.getElementById('deleteAccountModal');
  if (!deleteModal) return;

  const input = deleteModal.querySelector('input[name="confirmation"]');
  const submit = deleteModal.querySelector('button[type="submit"]');
  if (!input || !submit) return;

  function syncState() {
    submit.disabled = input.value.trim() !== 'DELETE';
  }

  input.addEventListener('input', syncState);
  deleteModal.addEventListener('shown.bs.modal', syncState);
  syncState();
})();
