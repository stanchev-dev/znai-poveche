(async function () {
  const meta = document.getElementById('post-page-meta');
  const postId = meta.dataset.postId;
  const appRoot = document.getElementById('app-root');
  const isAuthenticated = appRoot.dataset.authenticated === '1';
  const loginUrl = appRoot.dataset.loginUrl;

  const postAlert = document.getElementById('post-alert');
  const postContainer = document.getElementById('post-container');
  const commentsList = document.getElementById('comments-list');

  function chip(author) { return `<span class="badge bg-light text-dark">${author.username} (${author.display_name}, ниво ${author.level})</span>`; }
  function imgIf(url) { return url ? `<img src="${url}" class="img-fluid rounded mt-2" alt="image">` : ''; }
  function alertHtml(text, type='warning') { return `<div class="alert alert-${type}">${text}</div>`; }
  function loginAlert() { return `${alertHtml(`Трябва да сте логнати. <a href="${loginUrl}">Вход</a>`, 'warning')}`; }

  async function vote(url, scoreEl) {
    const res = await window.apiUtils.apiFetch(url, { method: 'POST', body: JSON.stringify({ value: 1 }) });
    if (res.status === 401 || res.status === 403) {
      postAlert.innerHTML = loginAlert();
      return;
    }
    const data = await res.json();
    if (data.score !== undefined) scoreEl.textContent = data.score;
  }

  async function voteDown(url, scoreEl) {
    const res = await window.apiUtils.apiFetch(url, { method: 'POST', body: JSON.stringify({ value: -1 }) });
    if (res.status === 401 || res.status === 403) {
      postAlert.innerHTML = loginAlert();
      return;
    }
    const data = await res.json();
    if (data.score !== undefined) scoreEl.textContent = data.score;
  }

  async function submitReport(targetType, targetId, reason, message) {
    const res = await window.apiUtils.apiFetch('/api/reports/', {
      method: 'POST',
      body: JSON.stringify({ target_type: targetType, target_id: targetId, reason, message })
    });
    const data = await res.json().catch(() => ({}));
    if (res.status === 401 || res.status === 403) {
      postAlert.innerHTML = loginAlert();
      return;
    }
    if (!res.ok) {
      const msg = data.non_field_errors?.[0] || data.detail || 'Грешка при докладване';
      postAlert.innerHTML = alertHtml(msg, 'danger');
      return;
    }
    postAlert.innerHTML = alertHtml('Докладът е изпратен.', 'success');
  }

  function reportFormHtml(type, id) {
    return `<div class="mt-2">
      <select class="form-select form-select-sm report-reason mb-1" data-target-type="${type}" data-target-id="${id}">
        <option value="spam">spam</option><option value="abuse">abuse</option><option value="off_topic">off_topic</option><option value="other">other</option>
      </select>
      <textarea class="form-control form-control-sm report-message mb-1" placeholder="Съобщение (по желание)"></textarea>
      <button class="btn btn-sm btn-outline-danger report-submit">Докладвай</button>
    </div>`;
  }

  async function loadPost() {
    const res = await window.apiUtils.apiFetch(`/api/posts/${postId}/`);
    if (res.status === 404) {
      postAlert.innerHTML = alertHtml('Не е намерено');
      document.getElementById('comment-form-wrap')?.remove();
      return;
    }
    if (res.status === 400) {
      postAlert.innerHTML = alertHtml('Невалидна заявка');
      return;
    }
    const post = await res.json();
    postContainer.innerHTML = `<div class="card"><div class="card-body">
      <h1 class="h4">${post.title}</h1>
      <p>${post.body}</p>
      ${imgIf(post.image)}
      <p>Точки: <strong id="post-score">${post.score}</strong></p>
      ${chip(post.author)}
      <div class="mt-2">
        <button class="btn btn-sm btn-success" id="post-up">▲</button>
        <button class="btn btn-sm btn-danger" id="post-down">▼</button>
      </div>
      ${reportFormHtml('post', post.id)}
    </div></div>`;

    const scoreEl = document.getElementById('post-score');
    document.getElementById('post-up').onclick = () => vote(`/api/posts/${postId}/vote/`, scoreEl);
    document.getElementById('post-down').onclick = () => voteDown(`/api/posts/${postId}/vote/`, scoreEl);
  }

  async function loadComments() {
    const res = await window.apiUtils.apiFetch(`/api/posts/${postId}/comments/`);
    if (!res.ok) {
      commentsList.innerHTML = alertHtml(res.status === 404 ? 'Не е намерено' : 'Невалидна заявка');
      return;
    }
    const items = await res.json();
    if (!items.length) {
      commentsList.innerHTML = '<div class="alert alert-info">Няма резултати</div>';
      return;
    }
    commentsList.innerHTML = items.map((c) => `<div class="card"><div class="card-body">
      <p>${c.body}</p>${imgIf(c.image)}
      <p>Точки: <strong id="comment-score-${c.id}">${c.score}</strong></p>
      ${chip(c.author)}
      <div class="mt-2">
        <button class="btn btn-sm btn-success comment-up" data-id="${c.id}">▲</button>
        <button class="btn btn-sm btn-danger comment-down" data-id="${c.id}">▼</button>
      </div>
      ${reportFormHtml('comment', c.id)}
    </div></div>`).join('');

    commentsList.querySelectorAll('.comment-up').forEach((btn) => {
      btn.onclick = () => vote(`/api/comments/${btn.dataset.id}/vote/`, document.getElementById(`comment-score-${btn.dataset.id}`));
    });
    commentsList.querySelectorAll('.comment-down').forEach((btn) => {
      btn.onclick = () => voteDown(`/api/comments/${btn.dataset.id}/vote/`, document.getElementById(`comment-score-${btn.dataset.id}`));
    });
  }

  document.addEventListener('click', (event) => {
    if (!event.target.classList.contains('report-submit')) return;
    const wrap = event.target.closest('div');
    const reasonEl = wrap.querySelector('.report-reason');
    const msgEl = wrap.querySelector('.report-message');
    submitReport(reasonEl.dataset.targetType, Number(reasonEl.dataset.targetId), reasonEl.value, msgEl.value);
  });

  const form = document.getElementById('comment-form');
  if (form) {
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const fd = new FormData();
      fd.append('body', document.getElementById('comment-body').value);
      const image = document.getElementById('comment-image').files[0];
      if (image) fd.append('image', image);
      const res = await window.apiUtils.apiFetch(`/api/posts/${postId}/comments/`, { method: 'POST', body: fd });
      if (res.status === 401 || res.status === 403) {
        postAlert.innerHTML = loginAlert();
        return;
      }
      if (!res.ok) {
        postAlert.innerHTML = alertHtml('Грешка при коментар', 'danger');
        return;
      }
      form.reset();
      loadComments();
    });
  }

  await loadPost();
  await loadComments();
})();
