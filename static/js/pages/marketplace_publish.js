(function () {
  const form = document.getElementById('listing-publish-form');
  const errorsBox = document.getElementById('publish-errors');
  const subjectSelect = document.getElementById('subject');
  const imageInlineError = document.getElementById('image-inline-error');
  if (!form || !errorsBox || !subjectSelect) return;

  function clearInlineImageError() {
    if (!imageInlineError) return;
    imageInlineError.textContent = '';
    imageInlineError.classList.add('d-none');
  }

  function setInlineImageError(message) {
    if (!imageInlineError) return;
    imageInlineError.textContent = message;
    imageInlineError.classList.remove('d-none');
  }

  function renderErrors(errorData) {
    const items = [];
    if (typeof errorData === 'string') {
      items.push(errorData);
    } else if (Array.isArray(errorData)) {
      errorData.forEach((entry) => items.push(String(entry)));
    } else if (errorData && typeof errorData === 'object') {
      Object.entries(errorData).forEach(([field, messages]) => {
        if (Array.isArray(messages)) {
          messages.forEach((msg) => items.push(`${field}: ${msg}`));
        } else {
          items.push(`${field}: ${messages}`);
        }
      });
    }

    if (!items.length) items.push('Възникна грешка при публикуване.');

    errorsBox.innerHTML = `
      <div class="alert alert-danger rounded-4 shadow-sm">
        <ul class="mb-0">${items.map((item) => `<li>${item}</li>`).join('')}</ul>
      </div>
    `;
  }

  async function loadSubjects() {
    const response = await window.apiUtils.apiFetch('/api/subjects/');
    if (!response.ok) {
      subjectSelect.innerHTML = '<option value="">Неуспешно зареждане</option>';
      return;
    }

    const subjects = await response.json();
    subjectSelect.innerHTML = '<option value="">Избери предмет</option>' + subjects
      .map((subject) => `<option value="${subject.slug}">${subject.name}</option>`)
      .join('');
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    errorsBox.innerHTML = '';
    clearInlineImageError();

    const payload = new FormData();
    payload.append('subject', form.subject.value);
    payload.append('price_per_hour', form.price_per_hour.value);
    payload.append('lesson_mode', form.lesson_mode.value);
    payload.append('description', form.description.value);
    payload.append('contact_name', form.contact_name.value);
    payload.append('contact_phone', form.contact_phone.value);

    const files = (window.marketplaceImages && window.marketplaceImages.files) || [];
    files.forEach((file) => payload.append('images', file));

    const response = await window.apiUtils.apiFetch('/api/listings/', {
      method: 'POST',
      body: payload,
    });

    if (response.ok) {
      window.location.assign('/marketplace/');
      return;
    }

    if (response.status === 400) {
      const errorData = await response.json();
      if (errorData && errorData.images && errorData.images.length) {
        setInlineImageError(String(errorData.images[0]));
      }
      renderErrors(errorData);
      return;
    }

    renderErrors('Сървърна грешка. Опитай отново.');
  });

  loadSubjects();
})();
