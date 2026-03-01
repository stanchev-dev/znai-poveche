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
  const reportBtn = document.querySelector('[data-report-btn]');
  const reportModalEl = document.getElementById('listing-report-modal');
  const reportReason = document.getElementById('listing-report-reason');
  const reportMessage = document.getElementById('listing-report-message');
  const reportSubmit = document.querySelector('[data-report-submit]');
  const lightbox = document.getElementById('listing-image-lightbox');
  const lightboxDialog = document.getElementById('listing-lightbox-dialog');
  const lightboxImage = document.getElementById('listing-lightbox-image');
  const lightboxClose = document.getElementById('listing-lightbox-close');
  const lightboxPrev = document.getElementById('listing-lightbox-prev');
  const lightboxNext = document.getElementById('listing-lightbox-next');
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
    if (value.startsWith('+')) return `+${value.slice(1).replace(/\D/g, '')}`;
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

  function alertHtml(message, type = 'warning') {
    return `<div class="alert alert-${type}" role="alert">${escapeHtml(message)}</div>`;
  }

  function animateSuccessAlert() {
    const successAlert = alertBox.querySelector('.alert-success');
    if (!successAlert) return;
    successAlert.classList.remove('alert-pop-highlight');
    void successAlert.offsetWidth;
    successAlert.classList.add('alert-pop-highlight');
  }

  const reportUrl = meta.dataset.reportUrl || '/api/reports/';

  async function submitReport() {
    try {
      const targetId = Number(reportBtn?.dataset.targetId || listingId);
      const targetType = reportBtn?.dataset.targetType || 'listing';
      const res = await window.apiUtils.apiFetch(reportUrl, {
        method: 'POST',
        body: JSON.stringify({
          target_type: targetType,
          target_id: targetId,
          reason: reportReason.value,
          message: reportMessage.value
        })
      });
      if (res.status === 401 || res.status === 403) {
        window.location.href = buildLoginRedirectUrl();
        return;
      }
      if (!res.ok) {
        alertBox.innerHTML = alertHtml('Неуспешно изпращане на репорт.', 'danger');
        return;
      }
      alertBox.innerHTML = alertHtml('Репортът ви е изпратен успешно.', 'success');
      animateSuccessAlert();
      reportReason.value = 'spam';
      reportMessage.value = '';
      bootstrap.Modal.getOrCreateInstance(reportModalEl).hide();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (error) {
      alertBox.innerHTML = alertHtml('Неуспешно изпращане на репорт.', 'danger');
    }
  }

  function revealPhone(phoneLabel) {
    const phoneHref = normalizePhoneForTel(phoneLabel);
    if (!phoneHref) return;
    callBtn.href = `tel:${phoneHref}`;
    callBtn.dataset.revealed = '1';
    callBtn.classList.add('revealed');
    callBtn.innerHTML = `<span class="call-cta-content"><i class="bi bi-telephone" aria-hidden="true"></i><span class="call-cta-number">${escapeHtml(phoneLabel)}</span></span>`;
    callBtn.setAttribute('aria-label', `Обади се на ${phoneLabel}`);
  }

  function renderGallery(images) {
    window.marketplaceImageViewer.init({
      root: gallery,
      images,
      defaultImage,
      lightbox,
      lightboxDialog,
      lightboxImage,
      lightboxClose,
      lightboxPrev,
      lightboxNext,
      imageAlt: 'Снимка на обява',
      lightboxAlt: 'Разширена снимка на обява'
    });
  }


  const res = await window.apiUtils.apiFetch(`/api/listings/${listingId}/`);
  if (res.status === 404) {
    alertBox.innerHTML = '<div class="alert alert-warning">Не е намерено</div>';
    detail.style.display = 'none';
    return;
  }

  const l = await res.json();
  const ownerDisplayName = l.owner.display_name || l.owner.username;
  const ownerSecondaryText = l.owner.display_name && l.owner.display_name !== l.owner.username ? `@${l.owner.username}` : '';
  const ownerLevel = Number.isFinite(Number(l.owner.level)) ? Number(l.owner.level) : null;
  const ownerAvatar = l.owner.avatar || l.owner.avatar_url || defaultImage;

  const imageUrls = (l.images || []).map((entry) => entry.image);
  if (!imageUrls.length && l.image) imageUrls.push(l.image);
  renderGallery(imageUrls);

  title.innerHTML = `${escapeHtml(l.subject.name)} ${l.is_vip ? '<span class="badge text-bg-warning align-middle">VIP</span>' : ''}`;
  description.innerHTML = l.description;
  owner.innerHTML = `<div class="card"><div class="card-body"><h2 class="h6 mb-3">Потребител</h2><div class="seller-card-header"><div class="seller-avatar"><img src="${escapeHtml(ownerAvatar)}" alt="Профилна снимка" class="rounded-circle">${ownerLevel !== null ? `<span class="seller-level-badge">${ownerLevel}</span>` : ''}</div><div class="seller-meta"><p class="seller-name">${escapeHtml(ownerDisplayName)}</p>${ownerSecondaryText ? `<p class="seller-subline mb-0">${escapeHtml(ownerSecondaryText)}</p>` : ''}</div></div><div class="seller-pills mb-0"><span class="badge rounded-pill listing-pill role-badge ${roleBadgeClass(l.owner.role)}">${escapeHtml(l.owner.role_label || (l.owner.role === 'teacher' ? 'Учител' : 'Учащ'))}</span>${l.lesson_mode_label ? `<span class="badge rounded-pill listing-pill lesson-mode-badge ${lessonModeBadgeClass(l.lesson_mode)}">${escapeHtml(l.lesson_mode_label)}</span>` : ''}</div></div></div>`;
  price.textContent = `${l.price_per_hour} €/ч`;

  reportBtn?.addEventListener('click', () => {
    if (!isAuthenticated) {
      window.location.href = buildLoginRedirectUrl();
      return;
    }
    bootstrap.Modal.getOrCreateInstance(reportModalEl).show();
  });

  reportSubmit?.addEventListener('click', submitReport);

  callBtn.addEventListener('click', async (event) => {
    if (!isAuthenticated) {
      event.preventDefault();
      window.location.href = buildLoginRedirectUrl();
      return;
    }
    if (callBtn.dataset.revealed === '1') return;
    event.preventDefault();
    if (!contactData) {
      const contactRes = await window.apiUtils.apiFetch(`/api/listings/${listingId}/contact/`);
      if (contactRes.status === 401 || contactRes.status === 403) {
        window.location.href = buildLoginRedirectUrl();
        return;
      }
      contactData = await contactRes.json();
    }
    if (!contactData.contact_phone) return;
    revealPhone(contactData.contact_phone);
  });
})();
