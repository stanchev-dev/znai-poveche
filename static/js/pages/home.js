(async function () {
  const list = document.getElementById('subjects-list');
  const alertBox = document.getElementById('subjects-alert');

  function showAlert(text, type = 'warning') {
    alertBox.innerHTML = `<div class="alert alert-${type}">${text}</div>`;
  }

  const res = await window.apiUtils.apiFetch('/api/subjects/');
  if (!res.ok) {
    showAlert('Невалидна заявка');
    return;
  }

  const subjects = await res.json();
  if (!subjects.length) {
    showAlert('Няма резултати', 'info');
    return;
  }

  list.innerHTML = subjects
    .map(
      (subject) => `
        <div class="col-12 col-sm-6 col-lg-4">
          <article class="card h-100 subject-card border-0 shadow-sm">
            <div class="card-body d-flex flex-column">
              <h3 class="h5 mb-3">${subject.name}</h3>
              <a class="btn btn-sm btn-outline-dark mt-auto align-self-start" href="/subjects/${subject.slug}/">Отвори</a>
            </div>
          </article>
        </div>
      `,
    )
    .join('');
})();
