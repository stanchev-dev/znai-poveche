(async function () {
  const list = document.getElementById('listings-list');
  const alertBox = document.getElementById('listings-alert');
  const subjectFilter = document.getElementById('subject-filter');
  const defaultAvatar = '/static/img/default-avatar.svg';
  let nextUrl = null;
  let prevUrl = null;

  function escapeHtml(value) {
    return String(value ?? '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#39;');
  }

  function avatarMarkup(owner) {
    const displayName = owner.display_name || owner.username;
    const initials = displayName
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((token) => token[0])
      .join('')
      .toUpperCase();
    return `
      <div class="listing-card-avatar-wrap" aria-hidden="true">
        <img src="${defaultAvatar}" alt="" class="listing-card-avatar" loading="lazy" onerror="this.style.display='none';this.nextElementSibling.classList.add('is-visible');">
        <div class="listing-card-avatar-placeholder">${escapeHtml(initials || 'У')}</div>
      </div>
    `;
  }

  function listingCard(l) {
    const detailsUrl = `/marketplace/${l.id}/`;
    return `
      <a href="${detailsUrl}" class="listing-card-link text-reset text-decoration-none" aria-label="Отвори обявата за ${escapeHtml(l.subject.name)}">
        <article class="card listing-card">
          <div class="listing-card-body">
            <div class="listing-card-left">${avatarMarkup(l.owner)}</div>
            <div class="listing-card-middle">
              <h2 class="listing-card-title h5 mb-2">Уроци по ${escapeHtml(l.subject.name)}</h2>
              <p class="listing-card-description mb-2">${escapeHtml(l.description_excerpt)}</p>
              <div class="listing-card-badges">
                <span class="badge rounded-pill text-bg-light border">${escapeHtml(l.subject.name)}</span>
                ${l.online_only ? '<span class="badge rounded-pill text-bg-info-subtle border">Онлайн</span>' : ''}
                ${l.is_vip ? '<span class="badge rounded-pill text-bg-warning border">ВИП</span>' : ''}
              </div>
            </div>
            <div class="listing-card-right">
              <div class="listing-card-price">${escapeHtml(l.price_per_hour)} лв./ч</div>
              <div class="listing-card-details">Детайли <span aria-hidden="true">→</span></div>
            </div>
          </div>
        </article>
      </a>
    `;
  }

  async function loadSubjects() {
    const res = await window.apiUtils.apiFetch('/api/subjects/');
    if (!res.ok) return;
    const subjects = await res.json();
    subjectFilter.innerHTML += subjects.map((s) => `<option value="${s.slug}">${s.name}</option>`).join('');
  }

  function buildUrl() {
    const subject = subjectFilter.value;
    const onlineOnly = document.getElementById('online-only').checked ? '1' : '0';
    const min = document.getElementById('price-min').value.trim();
    const max = document.getElementById('price-max').value.trim();
    let url = `/api/listings/?subject=${encodeURIComponent(subject)}&online_only=${onlineOnly}&page=1`;
    if (min) url += `&price_min=${encodeURIComponent(min)}`;
    if (max) url += `&price_max=${encodeURIComponent(max)}`;
    return url;
  }

  async function load(url) {
    alertBox.innerHTML = '';
    const res = await window.apiUtils.apiFetch(url);
    if (res.status === 404) {
      alertBox.innerHTML = '<div class="alert alert-warning">Не е намерено</div>';
      list.innerHTML = '';
      return;
    }
    if (res.status === 400) {
      alertBox.innerHTML = '<div class="alert alert-warning">Невалидна заявка</div>';
      return;
    }
    const data = await res.json();
    nextUrl = data.next;
    prevUrl = data.previous;
    if (!data.results.length) {
      list.innerHTML = '<div class="alert alert-info">Няма резултати</div>';
      return;
    }
    list.innerHTML = data.results.map((l) => listingCard(l)).join('');
  }

  document.getElementById('apply-filters').onclick = () => load(buildUrl());
  document.getElementById('prev-btn').onclick = () => { if (prevUrl) load(prevUrl); };
  document.getElementById('next-btn').onclick = () => { if (nextUrl) load(nextUrl); };

  await loadSubjects();
  await load(buildUrl());
})();
