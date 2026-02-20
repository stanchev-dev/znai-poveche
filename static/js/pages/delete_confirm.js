(function () {
  const form = document.getElementById('delete-confirm-form');
  if (!form) return;

  const submitBtn = document.getElementById('delete-confirm-submit');
  const errorBox = document.getElementById('delete-error-box');
  const redirectUrl = form.dataset.redirectUrl;

  function showError(message) {
    if (!errorBox) return;
    errorBox.innerHTML = `<div class="alert alert-danger" role="alert">${message}</div>`;
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (submitBtn?.disabled) return;

    if (submitBtn) {
      submitBtn.disabled = true;
    }

    try {
      const res = await window.apiUtils.apiFetch(window.location.href, {
        method: 'POST',
        body: new FormData(form)
      });

      if (!res.ok) {
        showError('Грешка при изтриване. Опитай отново.');
        return;
      }

      if (redirectUrl) {
        window.location.assign(redirectUrl);
        return;
      }

      document.body.innerHTML = '<main class="container py-5"><div class="alert alert-success">Изтрито успешно.</div></main>';
    } catch (_error) {
      showError('Грешка при изтриване. Опитай отново.');
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
      }
    }
  });
})();
