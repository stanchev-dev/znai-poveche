(function () {
  const form = document.getElementById('listing-publish-form');
  const errorsBox = document.getElementById('publish-errors');
  const subjectSelect = document.getElementById('subject');
  const imageInlineError = document.getElementById('image-inline-error');
  if (!form || !errorsBox || !subjectSelect) return;

  const PRIORITY_RULES = [
    {
      field: 'subject',
      message: 'Избери предмет.',
      isInvalid: () => !form.subject.value,
    },
    {
      field: 'price_per_hour',
      message: 'Въведи валидна цена на час (само число).',
      isInvalid: () => {
        const raw = (form.price_per_hour.value || '').trim();
        if (!raw) return true;
        if (!/^\d+(?:[\.,]\d{1,2})?$/.test(raw)) return true;
        return Number(raw.replace(',', '.')) < 0;
      },
    },
    {
      field: 'lesson_mode',
      message: 'Избери режим на обучение.',
      isInvalid: () => !form.querySelector('input[name="lesson_mode"]:checked'),
    },
    {
      field: 'description',
      message: 'Попълни описание.',
      isInvalid: () => (form.description.value || '').trim().length < 40,
    },
    {
      field: 'contact_name',
      message: 'Попълни лице за контакт.',
      isInvalid: () => !(form.contact_name.value || '').trim(),
    },
    {
      field: 'contact_phone',
      message: 'Въведи валиден телефон.',
      isInvalid: () => {
        const raw = (form.contact_phone.value || '').trim();
        const collapsed = raw.replace(/\s+/g, '');
        if (!collapsed) return true;
        if (collapsed.length < 9 || collapsed.length > 13) return true;
        if (!(collapsed.startsWith('0') || collapsed.startsWith('+359'))) return true;
        return !/^\+?\d+$/.test(collapsed);
      },
    },
  ];

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

  function clearFieldInvalidStates() {
    ['subject', 'price_per_hour', 'description', 'contact_name', 'contact_phone'].forEach((name) => {
      if (form[name]) form[name].classList.remove('is-invalid');
    });
    const radios = form.querySelectorAll('input[name="lesson_mode"]');
    radios.forEach((radio) => {
      const label = form.querySelector(`label[for="${radio.id}"]`);
      if (label) label.classList.remove('is-invalid');
    });
  }

  function markInvalidField(fieldName) {
    if (fieldName === 'lesson_mode') {
      const radios = form.querySelectorAll('input[name="lesson_mode"]');
      radios.forEach((radio) => {
        const label = form.querySelector(`label[for="${radio.id}"]`);
        if (label) label.classList.add('is-invalid');
      });
      return;
    }

    if (form[fieldName]) {
      form[fieldName].classList.add('is-invalid');
    }
  }

  function renderGlobalError(message) {
    errorsBox.innerHTML = `<div id="form-global-alert" class="alert alert-danger rounded-4 shadow-sm mb-4" role="alert">${message}</div>`;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function firstClientValidationFailure() {
    for (const rule of PRIORITY_RULES) {
      if (rule.isInvalid()) {
        return rule;
      }
    }
    return null;
  }

  function renderErrors(errorData) {
    if (errorData && typeof errorData === 'object') {
      const firstMessage = PRIORITY_RULES.map((rule) => {
        const fieldErrors = errorData[rule.field];
        if (Array.isArray(fieldErrors) && fieldErrors.length) {
          return String(fieldErrors[0]);
        }
        return null;
      }).find(Boolean);

      if (firstMessage) {
        renderGlobalError(firstMessage);
        return;
      }
    }

    renderGlobalError('Възникна грешка при публикуване.');
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
    clearFieldInvalidStates();

    const firstFailure = firstClientValidationFailure();
    if (firstFailure) {
      markInvalidField(firstFailure.field);
      renderGlobalError(firstFailure.message);
      return;
    }

    const payload = new FormData();
    payload.append('subject', form.subject.value);
    payload.append('price_per_hour', form.price_per_hour.value.trim());
    payload.append('lesson_mode', form.lesson_mode.value);
    payload.append('description', form.description.value);
    payload.append('contact_name', form.contact_name.value);
    payload.append('contact_phone', form.contact_phone.value);

    if (form.contact_email && form.contact_email.value.trim()) {
      payload.append('contact_email', form.contact_email.value.trim());
    }

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

    renderGlobalError('Сървърна грешка. Опитай отново.');
  });

  loadSubjects();
})();
