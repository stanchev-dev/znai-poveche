(function () {
  const input = document.getElementById('image');
  const tile = document.getElementById('listing-image-tile');
  const preview = document.getElementById('listing-image-preview');
  const placeholder = document.getElementById('listing-image-placeholder');
  const coverBadge = document.getElementById('listing-image-cover-badge');
  const removeBtn = document.getElementById('listing-image-remove');
  const errorBox = document.getElementById('image-inline-error');

  if (!input || !tile || !preview || !placeholder || !coverBadge || !removeBtn || !errorBox) {
    return;
  }

  const allowedTypes = ['image/jpeg', 'image/png'];
  const maxSizeBytes = 5 * 1024 * 1024;

  function clearError() {
    errorBox.textContent = '';
    errorBox.classList.add('d-none');
  }

  function setError(message) {
    errorBox.textContent = message;
    errorBox.classList.remove('d-none');
  }

  function resetPreview(clearInput) {
    preview.removeAttribute('src');
    preview.classList.add('d-none');
    placeholder.classList.remove('d-none');
    coverBadge.classList.add('d-none');
    removeBtn.classList.add('d-none');

    if (clearInput) {
      input.value = '';
    }
  }

  function showPreview(file) {
    const imageUrl = URL.createObjectURL(file);
    preview.src = imageUrl;
    preview.classList.remove('d-none');
    placeholder.classList.add('d-none');
    coverBadge.classList.remove('d-none');
    removeBtn.classList.remove('d-none');
    preview.onload = function () {
      URL.revokeObjectURL(imageUrl);
    };
  }

  tile.addEventListener('click', function () {
    input.click();
  });

  input.addEventListener('change', function () {
    clearError();

    if (!input.files || input.files.length === 0) {
      resetPreview(false);
      return;
    }

    const file = input.files[0];

    if (!allowedTypes.includes(file.type)) {
      resetPreview(true);
      setError('Невалиден файл. Разрешени са само .jpg, .jpeg и .png.');
      return;
    }

    if (file.size > maxSizeBytes) {
      resetPreview(true);
      setError('Файлът е прекалено голям. Максималният размер е 5MB.');
      return;
    }

    showPreview(file);
  });

  removeBtn.addEventListener('click', function (event) {
    event.preventDefault();
    event.stopPropagation();
    clearError();
    resetPreview(true);
  });
})();
