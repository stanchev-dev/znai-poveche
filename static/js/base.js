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
