(function () {
  const menu = document.getElementById('subjects-dropdown-menu');
  if (!menu) return;

  function renderSubjects(subjects) {
    if (!subjects.length) {
      menu.innerHTML = '<li><span class="dropdown-item-text text-muted">Няма резултати</span></li>';
      return;
    }
    menu.innerHTML = subjects.map((s) => (
      `<li><a class="dropdown-item" href="/subjects/${s.slug}/">${s.name}</a></li>`
    )).join('');
  }

  async function loadSubjects() {
    const cached = sessionStorage.getItem('subjects_cache');
    if (cached) {
      renderSubjects(JSON.parse(cached));
      return;
    }

    try {
      const res = await window.apiUtils.apiFetch('/api/subjects/');
      if (!res.ok) throw new Error('load-failed');
      const data = await res.json();
      sessionStorage.setItem('subjects_cache', JSON.stringify(data));
      renderSubjects(data);
    } catch (_e) {
      menu.innerHTML = '<li><span class="dropdown-item-text text-danger">Грешка при зареждане</span></li>';
    }
  }

  loadSubjects();
})();

(function () {
  const appRoot = document.getElementById('app-root');
  if (!appRoot) return;

  const TOP_MESSAGE_OFFSET = 320;
  const ALERT_SELECTOR = '.alert, [role="alert"]';

  function isTopPageMessage(alertEl) {
    if (!(alertEl instanceof HTMLElement) || !appRoot.contains(alertEl)) return false;

    const appRootTop = appRoot.getBoundingClientRect().top + window.scrollY;
    const alertTop = alertEl.getBoundingClientRect().top + window.scrollY;
    return alertTop - appRootTop <= TOP_MESSAGE_OFFSET;
  }

  function animateTopAlert(alertEl) {
    if (!isTopPageMessage(alertEl)) return;
    if (alertEl.dataset.topAlertAnimated === '1') return;

    alertEl.dataset.topAlertAnimated = '1';
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' });

    if (reduceMotion) return;
    alertEl.classList.remove('alert-pop-highlight');
    void alertEl.offsetWidth;
    alertEl.classList.add('alert-pop-highlight');
  }

  function processNode(node) {
    if (!(node instanceof HTMLElement)) return;

    if (node.matches(ALERT_SELECTOR)) {
      animateTopAlert(node);
    }

    node.querySelectorAll(ALERT_SELECTOR).forEach(animateTopAlert);
  }

  appRoot.querySelectorAll(ALERT_SELECTOR).forEach(animateTopAlert);

  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      mutation.addedNodes.forEach(processNode);
    });
  });

  observer.observe(appRoot, { childList: true, subtree: true });
})();
