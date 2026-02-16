(async function () {
  const list = document.getElementById('subjects-list');
  const alertBox = document.getElementById('subjects-alert');

  function showAlert(text, type = 'warning') {
    alertBox.innerHTML = `<div class="alert alert-${type}">${text}</div>`;
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#39;');
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
    .map((subject) => {
      const name = escapeHtml(subject.name);
      const slug = encodeURIComponent(subject.slug);
      const tileBg = subject.theme_color || '#5b6ee1';
      const imageMarkup = subject.tile_image
        ? `<img src="/static/${escapeHtml(subject.tile_image)}" class="subject-tile-ill" alt="" aria-hidden="true" loading="lazy" decoding="async" />`
        : '';

      return `
        <div class="col-12 col-md-6 col-xl-4">
          <a class="subject-tile text-decoration-none" href="/subjects/${slug}/" style="--tile-bg: ${escapeHtml(tileBg)};">
            <div class="subject-tile-content">
              <h3 class="subject-tile-title">${name}</h3>
            </div>
            ${imageMarkup}
          </a>
        </div>
      `;
    })
    .join('');
})();
