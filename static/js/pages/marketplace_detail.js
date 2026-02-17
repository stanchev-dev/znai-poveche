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
  const callBtn = document.getElementById('call-btn');
  const defaultImage = '/static/img/default-avatar.svg';
  let contactData = null;

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

  function normalizePhoneForTel(rawPhone) {
    const value = String(rawPhone || '').trim();
    if (!value) return '';

    if (value.startsWith('+')) {
      const clean = `+${value.slice(1).replace(/\D/g, '')}`;
      return clean.length > 1 ? clean : '';
    }

    const digits = value.replace(/\D/g, '');
    if (!digits) return '';
    if (digits.startsWith('00359')) return `+359${digits.slice(5)}`;
    if (digits.startsWith('359')) return `+${digits}`;
    if (digits.startsWith('0')) return `+359${digits.slice(1)}`;

    return `+${digits}`;
  }

  function buildLoginRedirectUrl() {
    const nextUrl = window.location.pathname + window.location.search;
    const separator = loginUrl.includes('?') ? '&' : '?';
    return `${loginUrl}${separator}next=${encodeURIComponent(nextUrl)}`;
  }

  function revealPhone(phoneLabel) {
    const phoneHref = normalizePhoneForTel(phoneLabel);
    if (!phoneHref) {
      return;
    }

    callBtn.href = `tel:${phoneHref}`;
    callBtn.dataset.revealed = '1';
    callBtn.classList.add('revealed');
    callBtn.innerHTML = `<span class="call-cta-content"><i class="bi bi-telephone" aria-hidden="true"></i><span class="call-cta-number">${escapeHtml(phoneLabel)}</span></span>`;
    callBtn.setAttribute('aria-label', `Обади се на ${phoneLabel}`);
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

  callBtn.addEventListener('click', async (event) => {
    if (!isAuthenticated) {
      event.preventDefault();
      window.location.href = buildLoginRedirectUrl();
      return;
    }

    if (callBtn.dataset.revealed === '1') {
      return;
    }

    event.preventDefault();

    if (!contactData) {
      const contactRes = await window.apiUtils.apiFetch(`/api/listings/${listingId}/contact/`);
      if (contactRes.status === 401 || contactRes.status === 403) {
        window.location.href = buildLoginRedirectUrl();
        return;
      }
      contactData = await contactRes.json();
    }

    if (!contactData.contact_phone) {
      return;
    }

    revealPhone(contactData.contact_phone);
  });
})();
