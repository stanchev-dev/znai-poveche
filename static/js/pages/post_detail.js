(async function () {
  const meta = document.getElementById('post-page-meta');
  const postId = meta.dataset.postId;
  const appRoot = document.getElementById('app-root');
  const isAuthenticated = appRoot.dataset.authenticated === '1';
  const loginUrl = appRoot.dataset.loginUrl;

  const postAlert = document.getElementById('post-alert');
  const postContainer = document.getElementById('post-container');
  const commentsList = document.getElementById('comments-list');

  function escapeHtml(value) {
    return String(value ?? '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#39;');
  }

  function formatRelativeTime(isoDate) {
    const date = new Date(isoDate);
    if (Number.isNaN(date.getTime())) return 'Публикувана наскоро';

    const diffMs = Date.now() - date.getTime();
    const minute = 60 * 1000;
    const hour = 60 * minute;
    const day = 24 * hour;

    if (diffMs < minute) return 'Публикувана преди по-малко от минута';

    if (diffMs < hour) {
      const minutes = Math.floor(diffMs / minute);
      return `Публикувана преди ${minutes} ${minutes === 1 ? 'минута' : 'минути'}`;
    }

    if (diffMs < day) {
      const hours = Math.floor(diffMs / hour);
      return `Публикувана преди ${hours} ${hours === 1 ? 'час' : 'часа'}`;
    }

    const days = Math.floor(diffMs / day);
    return `Публикувана преди ${days} ${days === 1 ? 'ден' : 'дни'}`;
  }

  function authorCard(author, subject) {
    const displayName = author.display_name || author.username;
    const secondary = author.display_name && author.display_name !== author.username ? `@${author.username}` : '';
    const level = Number.isFinite(Number(author.level)) ? Number(author.level) : null;
    const roleClass = author.role === 'teacher' ? 'role-badge--teacher' : 'role-badge--learner';
    const roleLabel = author.role_label || (author.role === 'teacher' ? 'Учител' : 'Учащ');
    const avatar = author.avatar || '/static/img/default-avatar.svg';

    return `
      <div class="card discussion-author-card">
        <div class="card-body">
          <div class="discussion-seller-card-header">
            <div class="discussion-seller-avatar">
              <img src="${avatar}" alt="Профилна снимка" class="rounded-circle">
              ${level !== null ? `<span class="discussion-seller-level-badge">${level}</span>` : ''}
            </div>
            <div class="discussion-seller-meta">
              <p class="discussion-seller-name">${escapeHtml(displayName)}</p>
              ${secondary ? `<p class="discussion-seller-subline mb-0">${escapeHtml(secondary)}</p>` : ''}
            </div>
          </div>
          <div class="discussion-seller-pills mb-0">
            <span class="badge rounded-pill listing-pill role-badge ${roleClass}">${escapeHtml(roleLabel)}</span>
            <span class="badge rounded-pill listing-pill subject-badge" style="${window.subjectBadgeUtils.getSubjectBadgeStyle(subject)}">${escapeHtml(subject.name)}</span>
          </div>
        </div>
      </div>
    `;
  }

  function imgIf(url) {
    return url
      ? `<div class="discussion-image-frame marketplace-detail-image-frame rounded mt-3"><img src="${escapeHtml(url)}" class="discussion-image marketplace-detail-image" alt="Илюстрация към дискусия"></div>`
      : '';
  }

  function alertHtml(text, type = 'warning') { return `<div class="alert alert-${type}">${text}</div>`; }
  function loginAlert() { return `${alertHtml(`Трябва да сте логнати. <a href="${loginUrl}">Вход</a>`, 'warning')}`; }

  async function castVote(url, scoreEl, targetType, voteValue, voteWrap) {
    if (targetType === 'post' && voteValue === -1) {
      const currentScore = Number(scoreEl.textContent || 0);
      if (currentScore <= 0) return;
    }

    const res = await window.apiUtils.apiFetch(url, { method: 'POST', body: JSON.stringify({ value: voteValue }) });
    if (res.status === 401 || res.status === 403) {
      postAlert.innerHTML = loginAlert();
      return;
    }

    const data = await res.json();
    const nextScore = data.score ?? data.new_score;
    if (nextScore !== undefined) scoreEl.textContent = nextScore;

    const voteState = Number(data.vote_value || voteValue);
    if (voteWrap) {
      voteWrap.querySelector('.vote-btn--up')?.classList.toggle('is-active', voteState === 1);
      voteWrap.querySelector('.vote-btn--down')?.classList.toggle('is-active', voteState === -1);
    }
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

    postContainer.innerHTML = `<article class="card discussion-post-card"><div class="card-body">
      <header class="discussion-post-header mb-3">
        <h1 class="h3 mb-2">${escapeHtml(post.title)}</h1>
        <div class="discussion-post-meta-row">
          <span><strong>${escapeHtml(post.author.display_name || post.author.username)}</strong></span>
          <span class="discussion-post-meta-separator">•</span>
          <span>${formatRelativeTime(post.created_at)}</span>
          <span class="discussion-post-meta-separator">•</span>
          <span class="badge rounded-pill listing-pill subject-badge" style="${window.subjectBadgeUtils.getSubjectBadgeStyle(post.subject)}">${escapeHtml(post.subject.name)}</span>
        </div>
      </header>

      <p class="discussion-post-description mb-0">${escapeHtml(post.body)}</p>
      ${imgIf(post.image)}

      <div class="discussion-post-voting mt-3" data-type="post">
        <button class="vote-btn vote-btn--up" id="post-up" aria-label="Положителен вот">▲</button>
        <strong id="post-score" class="vote-score">${post.score}</strong>
        <button class="vote-btn vote-btn--down" id="post-down" aria-label="Отрицателен вот">▼</button>
      </div>

      <section class="mt-3">
        <h2 class="h6 text-muted mb-2">Автор</h2>
        ${authorCard(post.author, post.subject)}
      </section>

      ${reportFormHtml('post', post.id)}
    </div></article>`;

    const scoreEl = document.getElementById('post-score');
    const voteWrap = postContainer.querySelector('.discussion-post-voting');
    document.getElementById('post-up').onclick = () => castVote(`/api/posts/${postId}/vote/`, scoreEl, 'post', 1, voteWrap);
    document.getElementById('post-down').onclick = () => castVote(`/api/posts/${postId}/vote/`, scoreEl, 'post', -1, voteWrap);
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
      <p>${escapeHtml(c.body)}</p>${imgIf(c.image)}
      <div class="discussion-post-voting mt-3" data-type="comment" id="comment-vote-${c.id}">
        <button class="vote-btn vote-btn--up comment-up" data-id="${c.id}" aria-label="Положителен вот">▲</button>
        <strong id="comment-score-${c.id}" class="vote-score">${c.score}</strong>
        <button class="vote-btn vote-btn--down comment-down" data-id="${c.id}" aria-label="Отрицателен вот">▼</button>
      </div>
      ${reportFormHtml('comment', c.id)}
    </div></div>`).join('');

    commentsList.querySelectorAll('.comment-up').forEach((btn) => {
      btn.onclick = () => castVote(`/api/comments/${btn.dataset.id}/vote/`, document.getElementById(`comment-score-${btn.dataset.id}`), 'comment', 1, document.getElementById(`comment-vote-${btn.dataset.id}`));
    });
    commentsList.querySelectorAll('.comment-down').forEach((btn) => {
      btn.onclick = () => castVote(`/api/comments/${btn.dataset.id}/vote/`, document.getElementById(`comment-score-${btn.dataset.id}`), 'comment', -1, document.getElementById(`comment-vote-${btn.dataset.id}`));
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
