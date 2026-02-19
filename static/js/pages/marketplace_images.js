(function () {
  const input = document.getElementById('images');
  const grid = document.getElementById('listing-images-grid');
  const errorBox = document.getElementById('image-inline-error');
  if (!input || !grid || !errorBox) return;

  const deletedInput = document.getElementById('deleted_image_ids');
  const orderingInput = document.getElementById('ordering_image_ids');
  const existingJsonNode = document.getElementById('existing-images-data');

  const maxFiles = 4;
  const allowedTypes = ['image/jpeg', 'image/png'];
  const maxSizeBytes = 2 * 1024 * 1024;
  const invalidFileMessage = 'Невалиден файл. Приемаме само jpg, jpeg, png до 2MB.';
  const maxFilesMessage = 'Можеш да качиш до 4 снимки.';

  const state = {
    existing: [],
    newFiles: [],
    deletedExistingIds: new Set(),
  };

  if (existingJsonNode && existingJsonNode.textContent.trim()) {
    try {
      state.existing = JSON.parse(existingJsonNode.textContent).map((entry) => ({
        id: entry.id,
        url: entry.url,
      }));
    } catch (_) {
      state.existing = [];
    }
  }

  function clearError() {
    errorBox.textContent = '';
    errorBox.classList.add('d-none');
  }

  function setError(message) {
    errorBox.textContent = message;
    errorBox.classList.remove('d-none');
  }

  function isValidType(file) {
    if (allowedTypes.includes(file.type)) return true;
    const name = (file.name || '').toLowerCase();
    return name.endsWith('.jpg') || name.endsWith('.jpeg') || name.endsWith('.png');
  }

  function syncInputFiles() {
    const transfer = new DataTransfer();
    state.newFiles.forEach((entry) => transfer.items.add(entry.file));
    input.files = transfer.files;

    if (deletedInput) {
      deletedInput.value = Array.from(state.deletedExistingIds).join(',');
    }
    if (orderingInput) {
      orderingInput.value = state.existing.map((entry) => String(entry.id)).join(',');
    }

    window.marketplaceImages = {
      files: state.newFiles.map((entry) => entry.file),
    };
  }

  function moveExistingToCover(index) {
    if (index <= 0 || index >= state.existing.length) return;
    const [entry] = state.existing.splice(index, 1);
    state.existing.unshift(entry);
    render();
  }

  function removeExisting(index) {
    const entry = state.existing[index];
    if (!entry) return;
    state.deletedExistingIds.add(entry.id);
    state.existing.splice(index, 1);
    clearError();
    render();
  }

  function removeNew(index) {
    const entry = state.newFiles[index];
    if (!entry) return;
    URL.revokeObjectURL(entry.url);
    state.newFiles.splice(index, 1);
    clearError();
    render();
  }

  function getImageTile(entry, index, kind) {
    const card = document.createElement('div');
    card.className = 'listing-image-card';

    const coverAction = index > 0 && kind === 'existing'
      ? '<button type="button" class="listing-cover-action" data-cover="1">Направи корица</button>'
      : '';

    card.innerHTML = `
      <img src="${entry.url}" alt="Снимка ${index + 1}" class="listing-image-thumb">
      ${index === 0 ? '<span class="badge text-bg-dark listing-cover-badge">КОРИЦА</span>' : ''}
      <button type="button" class="listing-remove-btn" data-remove="1" aria-label="Премахни снимката">&times;</button>
      ${coverAction}
    `;

    card.querySelector('[data-remove="1"]').addEventListener('click', () => {
      if (kind === 'existing') {
        removeExisting(index);
      } else {
        removeNew(index);
      }
    });

    const coverButton = card.querySelector('[data-cover="1"]');
    if (coverButton) {
      coverButton.addEventListener('click', () => moveExistingToCover(index));
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

    state.existing.forEach((entry, index) => grid.appendChild(getImageTile(entry, index, 'existing')));
    state.newFiles.forEach((entry, index) => grid.appendChild(getImageTile(entry, state.existing.length + index, 'new')));

    const total = state.existing.length + state.newFiles.length;
    if (total < maxFiles) {
      grid.appendChild(getAddTile());
    }

    const placeholders = Math.max(0, maxFiles - total - 1);
    for (let i = 0; i < placeholders; i += 1) {
      grid.appendChild(getPlaceholderTile());
    }

    syncInputFiles();
  }

  input.addEventListener('change', () => {
    clearError();
    const chosen = Array.from(input.files || []);
    if (!chosen.length) return;

    let hasInvalid = false;
    for (const file of chosen) {
      if (state.existing.length + state.newFiles.length >= maxFiles) {
        setError(maxFilesMessage);
        break;
      }

      if (!isValidType(file) || file.size > maxSizeBytes) {
        hasInvalid = true;
        continue;
      }

      state.newFiles.push({ file, url: URL.createObjectURL(file) });
    }

    if (hasInvalid) setError(invalidFileMessage);
    input.value = '';
    render();
  });

  render();
})();
