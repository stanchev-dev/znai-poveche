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

  list.innerHTML = subjects.map((subject) => `
    <div class="col-md-4">
      <div class="card h-100"><div class="card-body">
        <h2 class="h5">${subject.name}</h2>
        <a class="btn btn-sm btn-outline-primary" href="/subjects/${subject.slug}/">Отвори</a>
      </div></div>
    </div>
  `).join('');
})();
