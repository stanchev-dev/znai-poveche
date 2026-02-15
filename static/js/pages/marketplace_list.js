(async function () {
  const list = document.getElementById('listings-list');
  const alertBox = document.getElementById('listings-alert');
  const subjectFilter = document.getElementById('subject-filter');
  let nextUrl = null;
  let prevUrl = null;

  function chip(owner) { return `<span class="badge bg-light text-dark">${owner.username} (${owner.display_name}, ниво ${owner.level})</span>`; }

  async function loadSubjects() {
    const res = await window.apiUtils.apiFetch('/api/subjects/');
    if (!res.ok) return;
    const subjects = await res.json();
    subjectFilter.innerHTML += subjects.map((s) => `<option value="${s.slug}">${s.name}</option>`).join('');
  }

  function buildUrl() {
    const subject = subjectFilter.value;
    const onlineOnly = document.getElementById('online-only').checked ? '1' : '0';
    const min = document.getElementById('price-min').value.trim();
    const max = document.getElementById('price-max').value.trim();
    let url = `/api/listings/?subject=${encodeURIComponent(subject)}&online_only=${onlineOnly}&page=1`;
    if (min) url += `&price_min=${encodeURIComponent(min)}`;
    if (max) url += `&price_max=${encodeURIComponent(max)}`;
    return url;
  }

  async function load(url) {
    alertBox.innerHTML = '';
    const res = await window.apiUtils.apiFetch(url);
    if (res.status === 404) {
      alertBox.innerHTML = '<div class="alert alert-warning">Не е намерено</div>';
      list.innerHTML = '';
      return;
    }
    if (res.status === 400) {
      alertBox.innerHTML = '<div class="alert alert-warning">Невалидна заявка</div>';
      return;
    }
    const data = await res.json();
    nextUrl = data.next;
    prevUrl = data.previous;
    if (!data.results.length) {
      list.innerHTML = '<div class="alert alert-info">Няма резултати</div>';
      return;
    }
    list.innerHTML = data.results.map((l) => `<div class="card"><div class="card-body">
      <h2 class="h5">${l.subject.name} ${l.is_vip ? '<span class="badge text-bg-warning">VIP</span>' : ''}</h2>
      <p>${l.description_excerpt}</p>
      <p>Цена/час: <strong>${l.price_per_hour}</strong> | ${l.online_only ? 'Онлайн' : 'Присъствено'}</p>
      ${chip(l.owner)}
      <div class="mt-2"><a class="btn btn-sm btn-primary" href="/marketplace/${l.id}/">Детайли</a></div>
    </div></div>`).join('');
  }

  document.getElementById('apply-filters').onclick = () => load(buildUrl());
  document.getElementById('prev-btn').onclick = () => { if (prevUrl) load(prevUrl); };
  document.getElementById('next-btn').onclick = () => { if (nextUrl) load(nextUrl); };

  await loadSubjects();
  await load(buildUrl());
})();
