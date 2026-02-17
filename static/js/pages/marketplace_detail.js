(async function () {
  const meta = document.getElementById('listing-meta');
  const listingId = meta.dataset.listingId;
  const appRoot = document.getElementById('app-root');
  const isAuthenticated = appRoot.dataset.authenticated === '1';
  const loginUrl = appRoot.dataset.loginUrl;

  const alertBox = document.getElementById('listing-alert');
  const detail = document.getElementById('listing-detail');
  const gallery = document.getElementById('listing-gallery');
  const title = document.getElementById('listing-title');
  const description = document.getElementById('listing-description');
  const price = document.getElementById('listing-price');
  const owner = document.getElementById('listing-owner');
  const contactsWrap = document.getElementById('contacts-wrap');
  const contactsBtn = document.getElementById('contacts-btn');
  const defaultImage = '/static/img/default-avatar.svg';

  function escapeHtml(value) {
    return String(value ?? '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#39;');
  }

  function lessonModeBadgeClass(lessonMode) {
    if (lessonMode === 'online') return 'lesson-mode-badge--online';
    if (lessonMode === 'in_person') return 'lesson-mode-badge--in-person';
    return 'lesson-mode-badge--online-and-in-person';
  }

  function roleBadgeClass(role) {
    return role === 'teacher' ? 'role-badge--teacher' : 'role-badge--learner';
  }

  const res = await window.apiUtils.apiFetch(`/api/listings/${listingId}/`);
  if (res.status === 404) {
    alertBox.innerHTML = '<div class="alert alert-warning">Не е намерено</div>';
    detail.style.display = 'none';
    return;
  }
  if (res.status === 400) {
    alertBox.innerHTML = '<div class="alert alert-warning">Невалидна заявка</div>';
    detail.style.display = 'none';
    return;
  }

  const l = await res.json();
  gallery.innerHTML = `<div class="card marketplace-detail-gallery-card"><div class="card-body p-2 p-md-3">
    <img src="${l.image || defaultImage}" alt="Снимка на обява" class="img-fluid rounded marketplace-detail-image" onerror="this.src='${defaultImage}'">
  </div></div>`;

  title.innerHTML = `${escapeHtml(l.subject.name)} ${l.is_vip ? '<span class="badge text-bg-warning align-middle">VIP</span>' : ''}`;
  description.innerHTML = l.description;

  owner.innerHTML = `<div class="card"><div class="card-body">
    <h2 class="h6 mb-3">Потребител</h2>
    <div class="listing-card-badges mb-0">
      <span class="badge bg-light text-dark">${escapeHtml(l.owner.username)} (${escapeHtml(l.owner.display_name)}, ниво ${escapeHtml(l.owner.level)})</span>
      <span class="badge rounded-pill listing-pill role-badge ${roleBadgeClass(l.owner.role)}">${escapeHtml(l.owner.role_label || (l.owner.role === 'teacher' ? 'Учител' : 'Учащ'))}</span>
      <span class="badge rounded-pill listing-pill subject-badge" style="${window.subjectBadgeUtils.getSubjectBadgeStyle(l.subject)}">${escapeHtml(l.subject.name)}</span>
      ${l.lesson_mode_label ? `<span class="badge rounded-pill listing-pill lesson-mode-badge ${lessonModeBadgeClass(l.lesson_mode)}">${escapeHtml(l.lesson_mode_label)}</span>` : ''}
    </div>
  </div></div>`;

  price.textContent = `${l.price_per_hour} €/ч`;

  contactsBtn.onclick = async () => {
    if (!isAuthenticated) {
      contactsWrap.innerHTML = `<div class="alert alert-warning">Трябва да сте логнати. <a href="${loginUrl}">Вход</a></div>`;
      return;
    }
    const contactRes = await window.apiUtils.apiFetch(`/api/listings/${listingId}/contact/`);
    if (contactRes.status === 401 || contactRes.status === 403) {
      contactsWrap.innerHTML = `<div class="alert alert-warning">Трябва да сте логнати. <a href="${loginUrl}">Вход</a></div>`;
      return;
    }
    const c = await contactRes.json();
    let html = '<div class="card card-body"><h2 class="h6">Контакти</h2>';
    if (c.contact_phone) html += `<p>Телефон: ${c.contact_phone}</p>`;
    if (c.contact_email) html += `<p>Имейл: ${c.contact_email}</p>`;
    if (c.contact_url) html += `<p>Линк: <a href="${c.contact_url}" target="_blank">${c.contact_url}</a></p>`;
    if (!c.contact_phone && !c.contact_email && !c.contact_url) html += '<p>Няма резултати</p>';
    html += '</div>';
    contactsWrap.innerHTML = html;
  };
})();
