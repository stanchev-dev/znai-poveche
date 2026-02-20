(function () {
  function initMarketplaceImageViewer(options) {
    const {
      root,
      images,
      defaultImage = '/static/img/default-avatar.svg',
      lightbox,
      lightboxDialog,
      lightboxImage,
      lightboxClose,
      lightboxPrev,
      lightboxNext,
      imageAlt = 'Снимка',
      lightboxAlt = 'Разширена снимка'
    } = options || {};

    if (!root || !lightbox || !lightboxDialog || !lightboxImage || !lightboxClose || !lightboxPrev || !lightboxNext) {
      return;
    }

    const galleryImages = Array.isArray(images) ? images.filter(Boolean) : [];
    if (!galleryImages.length) {
      root.innerHTML = `<div class="card marketplace-detail-gallery-card"><div class="card-body p-2 p-md-3"><div class="marketplace-detail-image-frame rounded"><img src="${defaultImage}" alt="${imageAlt}" class="img-fluid marketplace-detail-image"></div></div></div>`;
      return;
    }

    let current = 0;

    function syncLightbox() {
      const currentImage = galleryImages[current] || galleryImages[0] || defaultImage;
      lightboxImage.src = currentImage;
      lightboxImage.alt = lightboxAlt;
      lightboxPrev.classList.toggle('d-none', galleryImages.length <= 1);
      lightboxNext.classList.toggle('d-none', galleryImages.length <= 1);
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
      lightboxClose.focus();
      document.body.classList.add('listing-lightbox-open');
    }

    function next() {
      current = (current + 1) % galleryImages.length;
      update();
    }

    function prev() {
      current = (current - 1 + galleryImages.length) % galleryImages.length;
      update();
    }

    function update() {
      const currentImage = galleryImages[current] || galleryImages[0] || defaultImage;
      mainImage.src = currentImage;
      thumbs.querySelectorAll('button').forEach((btn, index) => {
        btn.classList.toggle('active', index === current);
      });

      if (lightbox.classList.contains('is-open')) {
        syncLightbox();
      }
    }

    root.innerHTML = `
      <div class="card marketplace-detail-gallery-card">
        <div class="card-body p-2 p-md-3">
          <div class="marketplace-carousel" data-count="${galleryImages.length}">
            <button type="button" class="carousel-nav carousel-prev ${galleryImages.length === 1 ? 'd-none' : ''}" aria-label="Предишна снимка">&#10094;</button>
            <div class="marketplace-detail-image-frame rounded">
              <img class="img-fluid marketplace-detail-image" id="carousel-main-image" alt="${imageAlt}">
              <button type="button" class="listing-expand-btn" id="listing-expand-btn" aria-label="Разшири снимката">
                <i class="bi bi-arrows-fullscreen" aria-hidden="true"></i>
              </button>
            </div>
            <button type="button" class="carousel-nav carousel-next ${galleryImages.length === 1 ? 'd-none' : ''}" aria-label="Следваща снимка">&#10095;</button>
          </div>
          <div class="carousel-thumbs ${galleryImages.length <= 1 ? 'd-none' : ''}" id="carousel-thumbs"></div>
        </div>
      </div>`;

    const mainImage = root.querySelector('#carousel-main-image');
    const thumbs = root.querySelector('#carousel-thumbs');
    const expandBtn = root.querySelector('#listing-expand-btn');

    if (galleryImages.length > 1) {
      galleryImages.forEach((src, index) => {
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

      root.querySelector('.carousel-prev')?.addEventListener('click', prev);
      root.querySelector('.carousel-next')?.addEventListener('click', next);
    }

    lightboxPrev.onclick = (event) => {
      event.preventDefault();
      event.stopPropagation();
      if (galleryImages.length > 1) prev();
    };

    lightboxNext.onclick = (event) => {
      event.preventDefault();
      event.stopPropagation();
      if (galleryImages.length > 1) next();
    };

    lightboxClose.onclick = closeModal;
    lightboxDialog.onclick = (event) => event.stopPropagation();
    lightboxImage.onclick = (event) => event.stopPropagation();
    lightbox.onclick = (event) => {
      if (event.target === lightbox) {
        closeModal();
      }
    };

    expandBtn?.addEventListener('click', openModal);

    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && lightbox.classList.contains('is-open')) {
        closeModal();
        return;
      }

      if (!lightbox.classList.contains('is-open') || galleryImages.length <= 1) {
        return;
      }

      if (event.key === 'ArrowLeft') prev();
      if (event.key === 'ArrowRight') next();
    });

    update();
  }

  window.marketplaceImageViewer = {
    init: initMarketplaceImageViewer
  };
})();
