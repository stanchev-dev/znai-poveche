(function () {
  const input = document.getElementById('images');
  const grid = document.getElementById('listing-images-grid');
  const errorBox = document.getElementById('image-inline-error');
  if (!input || !grid || !errorBox) return;

  const maxFiles = 8;
  const allowedTypes = ['image/jpeg', 'image/png'];
  const maxSizeBytes = 5 * 1024 * 1024;
  const state = [];

  function clearError() {
    errorBox.textContent = '';
    errorBox.classList.add('d-none');
  }

  function setError(message) {
    errorBox.textContent = message;
    errorBox.classList.remove('d-none');
  }

  function syncInputFiles() {
    const transfer = new DataTransfer();
    state.forEach((entry) => transfer.items.add(entry.file));
    input.files = transfer.files;
    window.marketplaceImages = {
      files: state.map((entry) => entry.file),
      setAsCover,
      removeAt,
    };
  }

  function setAsCover(index) {
    if (index <= 0 || index >= state.length) return;
    const [selected] = state.splice(index, 1);
    state.unshift(selected);
    render();
  }

  function removeAt(index) {
    if (index < 0 || index >= state.length) return;
    state.splice(index, 1);
    render();
  }

  function getImageTile(entry, index) {
    const card = document.createElement('div');
    card.className = 'listing-image-card';
    card.innerHTML = `
      <img src="${entry.url}" alt="Снимка ${index + 1}" class="listing-image-thumb">
      ${index === 0 ? '<span class="badge text-bg-dark listing-cover-badge">КОРИЦА</span>' : ''}
      <button type="button" class="listing-remove-btn" data-remove="1" aria-label="Премахни снимката">&times;</button>
      ${index !== 0 ? '<button type="button" class="listing-cover-action" data-cover="1">Направи корица</button>' : ''}
    `;

    card.querySelector('[data-remove="1"]').addEventListener('click', () => removeAt(index));
    const coverBtn = card.querySelector('[data-cover="1"]');
    if (coverBtn) {
      coverBtn.addEventListener('click', () => setAsCover(index));
    }
    return card;
  }

  function getAddTile() {
    const card = document.createElement('button');
    card.type = 'button';
    card.className = 'listing-image-card listing-image-add';
    card.innerHTML = '<span><i class="bi bi-camera"></i><span>Добави снимка</span></span>';
    card.addEventListener('click', () => input.click());
    return card;
  }

  function getPlaceholderTile() {
    const card = document.createElement('div');
    card.className = 'listing-image-card listing-image-placeholder-tile';
    return card;
  }

  function render() {
    grid.innerHTML = '';
    state.forEach((entry, index) => grid.appendChild(getImageTile(entry, index)));

    if (state.length < maxFiles) {
      grid.appendChild(getAddTile());
    }

    const placeholders = Math.max(0, maxFiles - state.length - 1);
    for (let i = 0; i < placeholders; i += 1) {
      grid.appendChild(getPlaceholderTile());
    }

    syncInputFiles();
  }

  function validateFiles(files) {
    const valid = [];
    for (const file of files) {
      if (!allowedTypes.includes(file.type)) {
        setError('Невалиден файл. Разрешени са само .jpg, .jpeg и .png.');
        continue;
      }
      if (file.size > maxSizeBytes) {
        setError('Файлът е прекалено голям. Максималният размер е 5MB.');
        continue;
      }
      valid.push(file);
    }
    return valid;
  }

  input.addEventListener('change', () => {
    clearError();
    const chosen = Array.from(input.files || []);
    if (!chosen.length) return;

    const roomLeft = maxFiles - state.length;
    const accepted = validateFiles(chosen).slice(0, roomLeft);

    accepted.forEach((file) => {
      state.push({ file, url: URL.createObjectURL(file) });
    });

    if (chosen.length > roomLeft) {
      setError(`Максималният брой снимки е ${maxFiles}.`);
    }

    render();
  });

  render();
})();
