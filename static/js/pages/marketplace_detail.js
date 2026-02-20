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
  const reportBtn = document.getElementById('listing-report-btn');
  const reportModalEl = document.getElementById('listing-report-modal');
  const reportReason = document.getElementById('listing-report-reason');
  const reportMessage = document.getElementById('listing-report-message');
  const reportSubmit = document.getElementById('listing-report-submit');
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

  async function submitReport() {
    try {
      const res = await window.apiUtils.apiFetch('/api/reports/', {
        method: 'POST',
        body: JSON.stringify({
          target_type: 'listing',
          target_id: Number(listingId),
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
      reportMessage.value = '';
      bootstrap.Modal.getOrCreateInstance(reportModalEl).hide();
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
    if (!images.length) {
      gallery.innerHTML = `<div class="card marketplace-detail-gallery-card"><div class="card-body p-2 p-md-3"><div class="marketplace-detail-image-frame rounded"><img src="${defaultImage}" alt="Снимка на обява" class="img-fluid marketplace-detail-image"></div></div></div>`;
      return;
    }

    let current = 0;

    function syncLightbox() {
      const currentImage = images[current] || images[0] || defaultImage;
      lightboxImage.src = currentImage;
      lightboxPrev.classList.toggle('d-none', images.length <= 1);
      lightboxNext.classList.toggle('d-none', images.length <= 1);
    }

    function update() {
      const currentImage = images[current] || images[0];
      mainImage.src = currentImage || defaultImage;
      thumbs.querySelectorAll('button').forEach((btn, index) => {
        btn.classList.toggle('active', index === current);
      });
      if (lightbox.classList.contains('is-open')) {
        syncLightbox();
      }
    }

    function closeModal() {
      lightbox.classList.remove('is-open');
      lightbox.setAttribute('aria-hidden', 'true');
      document.body.classList.remove('listing-lightbox-open');
    }

    function openModal() {
      syncLightbox();
      lightbox.classList.add('is-open');
      lightbox.setAttribute('aria-hidden', 'false');
      document.body.classList.add('listing-lightbox-open');
      lightboxClose.focus();
    }

    function next() {
      current = (current + 1) % images.length;
      update();
    }

    function prev() {
      current = (current - 1 + images.length) % images.length;
      update();
    }

    function onLightboxPrev(event) {
      event.preventDefault();
      event.stopPropagation();
      prev();
    }

    function onLightboxNext(event) {
      event.preventDefault();
      event.stopPropagation();
      next();
    }

    gallery.innerHTML = `
      <div class="card marketplace-detail-gallery-card">
        <div class="card-body p-2 p-md-3">
          <div class="marketplace-carousel" data-count="${images.length}">
            <button type="button" class="carousel-nav carousel-prev ${images.length === 1 ? 'd-none' : ''}" aria-label="Предишна снимка">&#10094;</button>
            <div class="marketplace-detail-image-frame rounded">
              <img class="img-fluid marketplace-detail-image" id="carousel-main-image" alt="Снимка на обява">
              <button type="button" class="listing-expand-btn" id="listing-expand-btn" aria-label="Разшири снимката">
                <i class="bi bi-arrows-fullscreen" aria-hidden="true"></i>
              </button>
            </div>
            <button type="button" class="carousel-nav carousel-next ${images.length === 1 ? 'd-none' : ''}" aria-label="Следваща снимка">&#10095;</button>
          </div>
          <div class="carousel-thumbs ${images.length <= 1 ? 'd-none' : ''}" id="carousel-thumbs"></div>
        </div>
      </div>`;

    const mainImage = document.getElementById('carousel-main-image');
    const thumbs = document.getElementById('carousel-thumbs');
    const expandBtn = document.getElementById('listing-expand-btn');

    if (images.length > 1) {
      images.forEach((src, index) => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = `carousel-thumb ${index === 0 ? 'active' : ''}`;
        btn.innerHTML = `<img src="${src}" alt="Миниатюра ${index + 1}">`;
        btn.addEventListener('click', () => {
          current = index;
          update();
        });
        thumbs.appendChild(btn);
      });

      gallery.querySelector('.carousel-prev').addEventListener('click', prev);
      gallery.querySelector('.carousel-next').addEventListener('click', next);
      lightboxPrev.addEventListener('click', onLightboxPrev);
      lightboxNext.addEventListener('click', onLightboxNext);
    }

    lightboxClose.addEventListener('click', closeModal);
    lightboxDialog.addEventListener('click', (event) => {
      event.stopPropagation();
    });
    lightboxImage.addEventListener('click', (event) => {
      event.stopPropagation();
    });
    lightbox.addEventListener('click', (event) => {
      if (event.target === lightbox) {
        closeModal();
      }
    });

    expandBtn.addEventListener('click', openModal);

    window.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && lightbox.classList.contains('is-open')) {
        closeModal();
        return;
      }

      if (!lightbox.classList.contains('is-open')) {
        return;
      }

      if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') {
        return;
      }

      if (images.length <= 1) {
        return;
      }

      if (event.key === 'ArrowLeft') {
        prev();
      }
      if (event.key === 'ArrowRight') {
        next();
      }
    });

    update();
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
