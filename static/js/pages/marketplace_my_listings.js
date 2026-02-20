(function () {
  const utils = window.subjectBadgeUtils;
  const pageRoot = document.querySelector('section.discussions-header-card')?.parentElement;
  const listWrap = pageRoot?.querySelector('.vstack');
  const publishBtnHref = pageRoot?.querySelector('.discussions-cta-btn')?.getAttribute('href') || '/marketplace/publish/';
  const alertHost = document.getElementById('global-alert');

  function showAlert(message, type = 'danger') {
    if (!alertHost) return;
    alertHost.innerHTML = `<div class="alert alert-${type}" role="alert">${message}</div>`;
  }

  function renderEmptyState() {
    if (!pageRoot || pageRoot.querySelector('article') || pageRoot.querySelector('.my-listings-empty-state')) return;
    pageRoot.insertAdjacentHTML('beforeend', `
      <div class="card border-0 shadow-sm rounded-4 p-4 p-md-5 my-listings-empty-state">
        <h2 class="h4 mb-2">Нямаш активни обяви.</h2>
        <p class="text-muted mb-3">Създай първата си обява в Маркетплейс.</p>
        <div><a class="btn btn-brand-purple" href="${publishBtnHref}">+ Добави обява</a></div>
      </div>`;
  }

  if (utils) {
    document.querySelectorAll('.subject-badge[data-subject-name]').forEach((badge) => {
      const subject = {
        name: badge.dataset.subjectName,
        slug: badge.dataset.subjectSlug,
      };

      badge.style.cssText = utils.getSubjectBadgeStyle(subject);
    });
  }

  document.addEventListener('click', async (event) => {
    const deleteLink = event.target.closest('.my-listings-action-btn--danger');
    if (!deleteLink) return;

    event.preventDefault();
    if (deleteLink.dataset.submitting === '1') return;
    if (!window.confirm('Сигурен ли си, че искаш да изтриеш тази обява?')) return;

    const card = deleteLink.closest('article');
    deleteLink.dataset.submitting = '1';
    deleteLink.classList.add('disabled');
    deleteLink.setAttribute('aria-disabled', 'true');

    try {
      const res = await window.apiUtils.apiFetch(deleteLink.href, { method: 'POST' });
      if (!res.ok) {
        showAlert('Грешка при изтриване. Опитай отново.');
        return;
      }

      card?.remove();
      if (listWrap && !listWrap.querySelector('article')) {
        listWrap.remove();
      }
      renderEmptyState();
    } catch (_error) {
      showAlert('Грешка при изтриване. Опитай отново.');
    } finally {
      deleteLink.dataset.submitting = '0';
      deleteLink.classList.remove('disabled');
      deleteLink.removeAttribute('aria-disabled');
    }
  });
})();
