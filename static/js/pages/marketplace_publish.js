(function () {
  function initMarketplacePublishForm() {
    const form = document.getElementById('listing-publish-form');
    const errorsBox = document.getElementById('publish-errors');
    const subjectSelect = document.getElementById('subject');
    const imageInlineError = document.getElementById('image-inline-error');
    if (!form || !errorsBox || !subjectSelect) return;

    const touchedFields = new Set();

    const FIELD_RULES = {
      subject: {
        message: 'Избери предмет.',
        isValid: () => Boolean(form.subject.value),
      },
      price_per_hour: {
        message: 'Въведи валидна цена на час (само число).',
        isValid: () => {
          const raw = (form.price_per_hour.value || '').trim();
          if (!raw) return false;
          if (!/^\d+(?:[\.,]\d{1,2})?$/.test(raw)) return false;
          return Number(raw.replace(',', '.')) >= 0;
        },
      },
      lesson_mode: {
        message: 'Избери режим на обучение.',
        isValid: () => Boolean(form.querySelector('input[name="lesson_mode"]:checked')),
      },
      description: {
        message: 'Попълни описание.',
        isValid: () => (form.description.value || '').trim().length >= 20,
      },
      contact_name: {
        message: 'Попълни лице за контакт.',
        isValid: () => {
          const raw = (form.contact_name.value || '').trim();
          if (!raw) return false;
          const normalized = raw.replace(/[\s-]+/g, '');
          return !/^\d+$/.test(normalized);
        },
      },
      contact_phone: {
        message: 'Въведи валиден телефон.',
        isValid: () => {
          const raw = (form.contact_phone.value || '').trim();
          if (!raw) return false;
          const collapsed = raw.replace(/[\s-]+/g, '');
          const digitsOnly = collapsed.startsWith('+') ? collapsed.slice(1) : collapsed;
          if (!digitsOnly || digitsOnly.length < 9 || digitsOnly.length > 13) return false;
          if (!(collapsed.startsWith('0') || collapsed.startsWith('+359'))) return false;
          return /^\+?\d+$/.test(collapsed);
        },
      },
    };

    const PRIORITY_RULES = [
      { field: 'subject', ...FIELD_RULES.subject },
      { field: 'price_per_hour', ...FIELD_RULES.price_per_hour },
      { field: 'lesson_mode', ...FIELD_RULES.lesson_mode },
      { field: 'description', ...FIELD_RULES.description },
      { field: 'contact_name', ...FIELD_RULES.contact_name },
      { field: 'contact_phone', ...FIELD_RULES.contact_phone },
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

    function toggleFieldIcons(fieldName, isValid) {
      const wrap = form.querySelector(`[data-validation-field="${fieldName}"]`);
      if (!wrap) return;

      const invalidIcon = wrap.querySelector('.invalid-feedback-icon');
      const validIcon = wrap.querySelector('.publish-valid-icon');

      if (invalidIcon) {
        invalidIcon.classList.toggle('d-none', isValid);
      }
      if (validIcon) {
        validIcon.classList.toggle('d-none', !isValid);
      }
    }

    function setFieldState(fieldName, isValid) {
      const field = form[fieldName];
      if (!field) return;

      field.classList.remove('is-invalid', 'is-valid');
      field.classList.add(isValid ? 'is-valid' : 'is-invalid');
      toggleFieldIcons(fieldName, isValid);
    }

    function shouldApplyFieldState(fieldName) {
      return form.classList.contains('form-submitted') || touchedFields.has(fieldName);
    }

    function setLessonModeState(isValid) {
      const radios = form.querySelectorAll('input[name="lesson_mode"]');
      radios.forEach((radio) => {
        const label = form.querySelector(`label[for="${radio.id}"]`);
        if (label) {
          label.classList.remove('is-invalid', 'is-valid');
          label.classList.add(isValid ? 'is-valid' : 'is-invalid');
        }
      });
    }

    function clearFieldStates() {
      ['subject', 'price_per_hour', 'description', 'contact_name', 'contact_phone'].forEach((name) => {
        if (!form[name]) return;
        form[name].classList.remove('is-invalid', 'is-valid');
        toggleFieldIcons(name, false);
      });

      const radios = form.querySelectorAll('input[name="lesson_mode"]');
      radios.forEach((radio) => {
        const label = form.querySelector(`label[for="${radio.id}"]`);
        if (label) label.classList.remove('is-invalid', 'is-valid');
      });
    }

    function renderGlobalError(message) {
      errorsBox.innerHTML = `<div id="form-global-alert" class="alert alert-danger rounded-4 shadow-sm mb-4" role="alert">${message}</div>`;
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function firstClientValidationFailure() {
      for (const rule of PRIORITY_RULES) {
        if (!rule.isValid()) {
          return rule;
        }
      }
      return null;
    }

    function validateField(fieldName) {
      const rule = FIELD_RULES[fieldName];
      if (!rule) return true;
      const isValid = rule.isValid();

      if (!shouldApplyFieldState(fieldName)) {
        form[fieldName].classList.remove('is-invalid', 'is-valid');
        toggleFieldIcons(fieldName, false);
        return isValid;
      }

      setFieldState(fieldName, isValid);
      return isValid;
    }

    function bindLiveValidation() {
      ['subject', 'price_per_hour', 'description', 'contact_name', 'contact_phone'].forEach((fieldName) => {
        const field = form[fieldName];
        if (!field) return;

        ['input', 'change', 'blur'].forEach((eventName) => {
          field.addEventListener(eventName, () => {
            touchedFields.add(fieldName);
            validateField(fieldName);
          });
        });
      });

      const lessonModeInputs = form.querySelectorAll('input[name="lesson_mode"]');
      lessonModeInputs.forEach((input) => {
        input.addEventListener('change', () => {
          touchedFields.add('lesson_mode');
          setLessonModeState(FIELD_RULES.lesson_mode.isValid());
        });
      });
    }

    function initialValidationPass() {
      ['subject', 'price_per_hour', 'description', 'contact_name', 'contact_phone'].forEach((fieldName) => {
        validateField(fieldName);
      });
      setLessonModeState(FIELD_RULES.lesson_mode.isValid());
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
      form.classList.add('form-submitted');
      errorsBox.innerHTML = '';
      clearInlineImageError();
      clearFieldStates();
      initialValidationPass();

      const firstFailure = firstClientValidationFailure();
      if (firstFailure) {
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

    bindLiveValidation();
    loadSubjects();
  }

  document.addEventListener('DOMContentLoaded', initMarketplacePublishForm);
})();
