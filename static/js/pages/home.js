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

  const res = await window.apiUtils.apiFetch('/api/subjects/', { cache: 'no-store' });
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
      const iconPath = typeof subject.tile_image === 'string' && subject.tile_image.trim()
        ? subject.tile_image.trim().replace(/^\/+/, '')
        : `img/${subject.slug}.svg`;
      const tileBgDark = /^#[0-9A-Fa-f]{6}$/.test(subject.theme_color_dark || '')
        ? subject.theme_color_dark
        : '#2563EB';
      const tileBgLight = /^#[0-9A-Fa-f]{6}$/.test(subject.theme_color_light || '')
        ? subject.theme_color_light
        : '#60A5FA';
      return `
        <div class="col-12 col-md-6 col-xl-4">
          <a class="subject-tile text-decoration-none" data-subject-slug="${escapeHtml(subject.slug)}" href="/subjects/${slug}/" style="--c1: ${escapeHtml(tileBgDark)}; --c2: ${escapeHtml(tileBgLight)};">
            <div class="subject-tile-content">
              <img class="subject-tile-icon" src="/static/${escapeHtml(iconPath)}" alt="" aria-hidden="true" loading="lazy" />
              <h3 class="subject-tile-title">${name}</h3>
            </div>
          </a>
        </div>
      `;
    })
    .join('');
})();
