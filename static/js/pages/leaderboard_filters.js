(function () {
  const scopeInput = document.getElementById('scope-select');
  const subjectInput = document.getElementById('subject-select');
  const scopeTrigger = document.getElementById('scope-trigger');
  const subjectTrigger = document.getElementById('subject-trigger');
  const scopeMenu = scopeTrigger ? scopeTrigger.nextElementSibling : null;
  const subjectMenu = subjectTrigger ? subjectTrigger.nextElementSibling : null;
  const subjectWrap = document.getElementById('subject-filter-wrap');

  if (!scopeInput || !scopeTrigger || !scopeMenu || !subjectWrap || !subjectInput || !subjectTrigger || !subjectMenu) {
    return;
  }

  const defaultSubjectLabel = 'Избери предмет';

  const applyMenuState = function (menuEl, value) {
    const items = menuEl.querySelectorAll('.dropdown-item');
    let activeItem = null;

    items.forEach((item) => {
      const isActive = item.dataset.value === value;
      item.classList.toggle('active', isActive);
      if (isActive) {
        activeItem = item;
      }
    });

    return activeItem || items[0] || null;
  };

  const setControlValue = function (inputEl, triggerEl, menuEl, value, fallbackLabel) {
    inputEl.value = value;
    const activeItem = applyMenuState(menuEl, value);
    triggerEl.textContent = activeItem ? activeItem.textContent.trim() : fallbackLabel;
  };

  const syncSubjectAvailability = function () {
    const isSubject = scopeInput.value === 'subject';

    subjectWrap.classList.toggle('d-none', !isSubject);
    subjectWrap.setAttribute('aria-hidden', String(!isSubject));

    subjectTrigger.disabled = !isSubject;
    subjectTrigger.setAttribute('aria-disabled', String(!isSubject));

    if (!isSubject) {
      setControlValue(subjectInput, subjectTrigger, subjectMenu, '', defaultSubjectLabel);
    }
  };

  const bindMenu = function (menuEl, onSelect) {
    menuEl.addEventListener('click', function (event) {
      const item = event.target.closest('.dropdown-item');
      if (!item) {
        return;
      }

      event.preventDefault();
      onSelect(item.dataset.value || '');
    });
  };

  bindMenu(scopeMenu, function (value) {
    setControlValue(scopeInput, scopeTrigger, scopeMenu, value, 'Глобална');
    syncSubjectAvailability();
  });

  bindMenu(subjectMenu, function (value) {
    setControlValue(subjectInput, subjectTrigger, subjectMenu, value, defaultSubjectLabel);
  });

  setControlValue(scopeInput, scopeTrigger, scopeMenu, scopeInput.value || 'global', 'Глобална');
  setControlValue(subjectInput, subjectTrigger, subjectMenu, subjectInput.value || '', defaultSubjectLabel);
  syncSubjectAvailability();
})();
