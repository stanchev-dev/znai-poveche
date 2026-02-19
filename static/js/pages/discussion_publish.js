(function () {
  function initDiscussionPublishForm() {
    const form = document.getElementById('post-publish-form');
    const errorsBox = document.getElementById('publish-errors');
    const subjectSelect = document.getElementById('subject');
    const prefillSubject = JSON.parse(document.getElementById('prefill-subject').textContent || '""');
    if (!form || !errorsBox || !subjectSelect) return;

    const touchedFields = new Set();
    const FIELD_RULES = {
      subject: {
        message: 'Избери предмет.',
        isValid: () => Boolean(form.subject.value),
      },
      title: {
        message: 'Добави заглавие.',
        isValid: () => (form.title.value || '').trim().length >= 3,
      },
      body: {
        message: 'Описанието трябва да е поне 20 символа.',
        isValid: () => (form.body.value || '').trim().length >= 20,
      },
    };

    const PRIORITY_RULES = [
      { field: 'subject', ...FIELD_RULES.subject },
      { field: 'title', ...FIELD_RULES.title },
      { field: 'body', ...FIELD_RULES.body },
    ];

    function renderGlobalError(message) {
      errorsBox.innerHTML = `<div class="alert alert-danger rounded-4 shadow-sm mb-3" role="alert">${message}</div>`;
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function toggleFieldUi(fieldName, isValid) {
      const wrap = form.querySelector(`[data-validation-field="${fieldName}"]`);
      const feedback = document.getElementById(`${fieldName}-feedback`);
      if (!wrap) return;

      const validIcon = wrap.querySelector('.publish-valid-icon');
      const invalidIcon = wrap.querySelector('.invalid-feedback-icon');

      if (validIcon) validIcon.classList.toggle('d-none', !isValid);
      if (invalidIcon) invalidIcon.classList.toggle('d-none', isValid);
      if (feedback) feedback.classList.toggle('d-none', isValid);
    }

    function shouldApply(fieldName) {
      return form.classList.contains('form-submitted') || touchedFields.has(fieldName);
    }

    function validateField(fieldName) {
      const rule = FIELD_RULES[fieldName];
      if (!rule || !form[fieldName]) return true;

      const isValid = rule.isValid();
      const field = form[fieldName];

      field.classList.remove('is-valid', 'is-invalid');
      if (!shouldApply(fieldName)) {
        toggleFieldUi(fieldName, true);
        const wrap = form.querySelector(`[data-validation-field="${fieldName}"]`);
        if (wrap) {
          wrap.querySelector('.publish-valid-icon')?.classList.add('d-none');
          wrap.querySelector('.invalid-feedback-icon')?.classList.add('d-none');
        }
        const feedback = document.getElementById(`${fieldName}-feedback`);
        if (feedback) feedback.classList.add('d-none');
        return isValid;
      }

      field.classList.add(isValid ? 'is-valid' : 'is-invalid');
      toggleFieldUi(fieldName, isValid);
      return isValid;
    }

    function firstFailure() {
      return PRIORITY_RULES.find((rule) => !rule.isValid()) || null;
    }

    function bindLiveValidation() {
      ['subject', 'title', 'body'].forEach((fieldName) => {
        const field = form[fieldName];
        if (!field) return;
        ['input', 'change', 'blur'].forEach((eventName) => {
          field.addEventListener(eventName, () => {
            touchedFields.add(fieldName);
            validateField(fieldName);
          });
        });
      });
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

      if (prefillSubject && subjects.some((subject) => subject.slug === prefillSubject)) {
        subjectSelect.value = prefillSubject;
      }
    }

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      form.classList.add('form-submitted');
      errorsBox.innerHTML = '';

      ['subject', 'title', 'body'].forEach(validateField);
      const invalid = firstFailure();
      if (invalid) {
        renderGlobalError(invalid.message);
        return;
      }

      const payload = new FormData();
      payload.append('subject', form.subject.value);
      payload.append('title', form.title.value.trim());
      payload.append('body', form.body.value.trim());

      const files = (window.marketplaceImages && window.marketplaceImages.files) || [];
      if (files.length) {
        payload.append('image', files[0]);
      }

      const response = await window.apiUtils.apiFetch('/api/posts/', {
        method: 'POST',
        body: payload,
      });

      if (response.ok) {
        window.location.assign(`/subjects/${encodeURIComponent(form.subject.value)}/`);
        return;
      }

      if (response.status === 400) {
        const data = await response.json();
        const firstMessage = PRIORITY_RULES
          .map((rule) => (Array.isArray(data[rule.field]) ? String(data[rule.field][0]) : null))
          .find(Boolean);
        renderGlobalError(firstMessage || 'Възникна грешка при публикуване.');
        return;
      }

      renderGlobalError('Сървърна грешка. Опитай отново.');
    });

    bindLiveValidation();
    loadSubjects();
  }

  document.addEventListener('DOMContentLoaded', initDiscussionPublishForm);
})();
