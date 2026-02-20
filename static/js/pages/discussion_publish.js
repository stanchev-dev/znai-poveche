(function () {
  function initDiscussionPublishForm() {
    const form = document.getElementById('post-publish-form');
    const errorsBox = document.getElementById('publish-errors');
    const subjectSelect = document.getElementById('subject');
    const subjectTrigger = document.getElementById('subject-trigger');
    const subjectMenu = form?.querySelector('#subject-trigger + .publish-select-menu');
    const gradeSelect = document.getElementById('grade');
    const gradeTrigger = document.getElementById('grade-trigger');
    const gradeMenu = form?.querySelector('#grade-trigger + .publish-select-menu');
    const prefillSubject = JSON.parse(document.getElementById('prefill-subject').textContent || '""');
    if (!form || !errorsBox || !subjectSelect || !subjectTrigger || !subjectMenu) return;

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

    function fieldControl(fieldName) {
      const field = form[fieldName];
      if (!field) return null;
      const proxySelector = field.getAttribute('data-validation-proxy');
      if (proxySelector) {
        return form.querySelector(proxySelector) || field;
      }
      return field;
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
      const field = fieldControl(fieldName);
      if (!rule || !field) return true;

      const isValid = rule.isValid();

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

    function bindCustomSelect(selectEl, triggerEl, menuEl) {
      if (!selectEl || !triggerEl || !menuEl) return;
      menuEl.addEventListener('click', (event) => {
        const option = event.target.closest('.dropdown-item[data-value]');
        if (!option) return;
        event.preventDefault();
        selectEl.value = option.dataset.value;
        triggerEl.textContent = option.textContent.trim();
        selectEl.dispatchEvent(new Event('change', { bubbles: true }));
      });
    }

    async function loadSubjects() {
      const response = await window.apiUtils.apiFetch('/api/subjects/');
      if (!response.ok) {
        subjectTrigger.textContent = 'Неуспешно зареждане';
        subjectMenu.innerHTML = '<li><span class="dropdown-item disabled">Неуспешно зареждане</span></li>';
        return;
      }

      const subjects = await response.json();
      subjectMenu.innerHTML = '<li><button type="button" class="dropdown-item" data-value="">Избери предмет</button></li>' + subjects
        .map((subject) => `<li><button type="button" class="dropdown-item" data-value="${subject.slug}">${subject.name}</button></li>`)
        .join('');
      subjectTrigger.textContent = 'Избери предмет';

      if (prefillSubject && subjects.some((subject) => subject.slug === prefillSubject)) {
        const prefill = subjects.find((subject) => subject.slug === prefillSubject);
        subjectSelect.value = prefillSubject;
        subjectTrigger.textContent = prefill.name;
      }
    }

    bindCustomSelect(subjectSelect, subjectTrigger, subjectMenu);
    bindCustomSelect(gradeSelect, gradeTrigger, gradeMenu);

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
      if (form.grade && form.grade.value) {
        payload.append('grade', form.grade.value);
      }

      const files = (window.marketplaceImages && window.marketplaceImages.files) || [];
      if (files.length) {
        payload.append('image', files[0]);
        files.forEach((file) => payload.append('images', file));
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
