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

  function imageMarkup(listing) {
    const imageUrl = listing.image || defaultAvatar;
    return `
      <div class="listing-card-avatar-wrap" aria-hidden="true">
        <img src="${escapeHtml(imageUrl)}" alt="" class="listing-card-avatar" loading="lazy" onerror="this.src='${defaultAvatar}'">
      </div>
    `;
  }

  function roleBadge(owner) {
    const roleLabel = owner.role_label || (owner.role === 'teacher' ? 'Учител' : 'Учащ');
    const roleClass = owner.role === 'teacher' ? 'role-badge--teacher' : 'role-badge--learner';
    return `<span class="badge rounded-pill listing-pill role-badge ${roleClass}">${escapeHtml(roleLabel)}</span>`;
  }

  function lessonModeBadgeClass(lessonMode) {
    if (lessonMode === 'online') return 'lesson-mode-badge--online';
    if (lessonMode === 'in_person') return 'lesson-mode-badge--in-person';
    return 'lesson-mode-badge--online-and-in-person';
  }

  function lessonModeBadge(listing) {
    if (!listing.lesson_mode_label) return '';
    return `<span class="badge rounded-pill listing-pill lesson-mode-badge ${lessonModeBadgeClass(listing.lesson_mode)}">${escapeHtml(listing.lesson_mode_label)}</span>`;
  }


  function subjectBadgeStyle(subject) {
    const dark = /^#[0-9A-Fa-f]{6}$/.test(subject?.theme_color_dark || '')
      ? subject.theme_color_dark
      : '#6F2CF3';
    const light = /^#[0-9A-Fa-f]{6}$/.test(subject?.theme_color_light || '')
      ? subject.theme_color_light
      : '#9465FF';
    return `--subject-badge-bg: ${escapeHtml(dark)}; --subject-badge-border: ${escapeHtml(light)};`;
  }

  function listingCard(l) {
    const detailsUrl = `/marketplace/${l.id}/`;
    return `
      <a href="${detailsUrl}" class="listing-card-link text-reset text-decoration-none" aria-label="Отвори обявата за ${escapeHtml(l.subject.name)}">
        <article class="card listing-card">
          <div class="listing-card-body">
            <div class="listing-card-left">${imageMarkup(l)}</div>
            <div class="listing-card-middle">
              <h2 class="listing-card-title h5 mb-2">Уроци по ${escapeHtml(l.subject.name)}</h2>
              <p class="listing-card-description mb-2">${escapeHtml(l.description_excerpt)}</p>
              <div class="listing-card-badges">
                <span class="badge rounded-pill listing-pill subject-badge subject-badge--default" style="${subjectBadgeStyle(l.subject)}">${escapeHtml(l.subject.name)}</span>
                ${lessonModeBadge(l)}
                ${l.is_vip ? '<span class="badge rounded-pill text-bg-warning border">ВИП</span>' : ''}
                ${roleBadge(l.owner)}
              </div>
            </div>
            <div class="listing-card-right">
              <div class="listing-card-price">${escapeHtml(l.price_per_hour)} €/ч</div>
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
