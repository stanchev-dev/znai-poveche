(async function () {
  const meta = document.getElementById('listing-meta');
  const listingId = meta.dataset.listingId;
  const appRoot = document.getElementById('app-root');
  const isAuthenticated = appRoot.dataset.authenticated === '1';
  const loginUrl = appRoot.dataset.loginUrl;

  const alertBox = document.getElementById('listing-alert');
  const detail = document.getElementById('listing-detail');
  const contactsWrap = document.getElementById('contacts-wrap');
  const defaultImage = '/static/img/default-avatar.svg';

  const res = await window.apiUtils.apiFetch(`/api/listings/${listingId}/`);
  if (res.status === 404) {
    alertBox.innerHTML = '<div class="alert alert-warning">Не е намерено</div>';
    document.getElementById('contacts-btn').style.display = 'none';
    return;
  }
  if (res.status === 400) {
    alertBox.innerHTML = '<div class="alert alert-warning">Невалидна заявка</div>';
    return;
  }
  const l = await res.json();
  detail.innerHTML = `<div class="card"><div class="card-body">
    <div class="mb-3"><img src="${l.image || defaultImage}" alt="Снимка на обява" class="img-fluid rounded" style="max-height:260px;object-fit:cover;" onerror="this.src='${defaultImage}'"></div>
    <h1 class="h4">${l.subject.name} ${l.is_vip ? '<span class="badge text-bg-warning">VIP</span>' : ''} ${l.lesson_mode_label ? `<span class="badge rounded-pill lesson-mode-badge">${l.lesson_mode_label}</span>` : ''}</h1>
    <p>${l.description}</p>
    <p>Цена/час: <strong>${l.price_per_hour} €/ч</strong></p>
    <p>Автор: <span class="badge bg-light text-dark">${l.owner.username} (${l.owner.display_name}, ниво ${l.owner.level})</span> <span class="badge rounded-pill text-bg-light border">${l.owner.role_label || (l.owner.role === "teacher" ? "Учител" : "Учащ")}</span></p>
  </div></div>`;

  document.getElementById('contacts-btn').onclick = async () => {
    if (!isAuthenticated) {
      contactsWrap.innerHTML = `<div class="alert alert-warning">Трябва да сте логнати. <a href="${loginUrl}">Вход</a></div>`;
      return;
    }
    const contactRes = await window.apiUtils.apiFetch(`/api/listings/${listingId}/contact/`);
    if (contactRes.status === 401 || contactRes.status === 403) {
      contactsWrap.innerHTML = `<div class="alert alert-warning">Трябва да сте логнати. <a href="${loginUrl}">Вход</a></div>`;
      return;
    }
    const c = await contactRes.json();
    let html = '<div class="card card-body"><h2 class="h6">Контакти</h2>';
    if (c.contact_phone) html += `<p>Телефон: ${c.contact_phone}</p>`;
    if (c.contact_email) html += `<p>Имейл: ${c.contact_email}</p>`;
    if (c.contact_url) html += `<p>Линк: <a href="${c.contact_url}" target="_blank">${c.contact_url}</a></p>`;
    if (!c.contact_phone && !c.contact_email && !c.contact_url) html += '<p>Няма резултати</p>';
    html += '</div>';
    contactsWrap.innerHTML = html;
  };
})();
