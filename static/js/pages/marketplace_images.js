(function () {
  const input = document.getElementById('images');
  const grid = document.getElementById('listing-images-grid');
  const errorBox = document.getElementById('image-inline-error');
  if (!input || !grid || !errorBox) return;

  const maxFiles = 4;
  const allowedTypes = ['image/jpeg', 'image/png'];
  const maxSizeBytes = 2 * 1024 * 1024;
  const invalidFileMessage = 'Невалиден файл. Приемаме само jpg, jpeg, png до 2MB.';
  const maxFilesMessage = 'Можеш да качиш до 4 снимки.';
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
      removeAt,
    };
  }

  function removeAt(index) {
    if (index < 0 || index >= state.length) return;
    URL.revokeObjectURL(state[index].url);
    state.splice(index, 1);
    clearError();
    render();
  }

  function getImageTile(entry, index) {
    const card = document.createElement('div');
    card.className = 'listing-image-card';
    card.innerHTML = `
      <img src="${entry.url}" alt="Снимка ${index + 1}" class="listing-image-thumb">
      ${index === 0 ? '<span class="badge text-bg-dark listing-cover-badge">КОРИЦА</span>' : ''}
      <button type="button" class="listing-remove-btn" data-remove="1" aria-label="Премахни снимката">&times;</button>
    `;

    card.querySelector('[data-remove="1"]').addEventListener('click', () => removeAt(index));
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

  function isValidType(file) {
    if (allowedTypes.includes(file.type)) return true;
    const name = (file.name || '').toLowerCase();
    return name.endsWith('.jpg') || name.endsWith('.jpeg') || name.endsWith('.png');
  }

  input.addEventListener('change', () => {
    clearError();
    const chosen = Array.from(input.files || []);
    if (!chosen.length) return;

    let hasInvalid = false;
    for (const file of chosen) {
      if (state.length >= maxFiles) {
        setError(maxFilesMessage);
        break;
      }

      if (!isValidType(file) || file.size > maxSizeBytes) {
        hasInvalid = true;
        continue;
      }

      state.push({ file, url: URL.createObjectURL(file) });
    }

    if (hasInvalid) {
      setError(invalidFileMessage);
    }

    if (chosen.length && state.length >= maxFiles && chosen.length > 0) {
      const acceptedNow = chosen.filter((file) => isValidType(file) && file.size <= maxSizeBytes).length;
      if (acceptedNow < chosen.length && !hasInvalid) {
        setError(maxFilesMessage);
      }
    }

    input.value = '';
    render();
  });

  render();
})();
