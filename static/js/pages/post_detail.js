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

  async function castVote(url, scoreEl, targetType, voteValue, voteWrap, targetId) {
    if (targetType === 'post' && voteValue === -1) {
      const currentScore = Number(scoreEl.textContent || 0);
      if (currentScore <= 0) return;
    }

    try {
      const res = await window.apiUtils.apiFetch(url, { method: 'POST', body: JSON.stringify({ value: voteValue }) });
      if (res.status === 401 || res.status === 403) {
        postAlert.innerHTML = loginAlert();
        return;
      }

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const msg = data.detail || data.non_field_errors?.[0] || 'Грешка при гласуване';
        postAlert.innerHTML = alertHtml(msg, 'danger');
        return;
      }

      const nextScore = data.score ?? data.new_score;
      if (nextScore !== undefined && scoreEl) {
        scoreEl.textContent = nextScore;
      } else if (targetType === 'post' && scoreEl) {
        const postRes = await window.apiUtils.apiFetch(`/api/posts/${targetId}/`);
        if (postRes.ok) {
          const postData = await postRes.json().catch(() => ({}));
          if (postData.score !== undefined) scoreEl.textContent = postData.score;
        }
      }

      const voteState = Number(data.vote_value ?? voteValue);
      if (voteWrap) {
        voteWrap.querySelector('.vote-btn--up')?.classList.toggle('is-active', voteState === 1);
        voteWrap.querySelector('.vote-btn--down')?.classList.toggle('is-active', voteState === -1);
      }
    } catch (error) {
      postAlert.innerHTML = alertHtml('Грешка при гласуване', 'danger');
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
    const collapseId = `report-collapse-${type}-${id}`;
    return `
      <div class="discussion-post-actions mt-3">
        <div class="discussion-post-voting" data-type="${type}" id="${type}-vote-${id}"></div>
        <button
          class="btn btn-sm btn-outline-danger discussion-report-toggle"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#${collapseId}"
          aria-expanded="false"
          aria-controls="${collapseId}"
        >Докладвай</button>
      </div>
      <div class="collapse mt-2" id="${collapseId}">
        <div class="discussion-report-box">
          <select class="form-select form-select-sm report-reason mb-2" data-target-type="${type}" data-target-id="${id}">
            <option value="spam">spam</option><option value="abuse">abuse</option><option value="off_topic">off_topic</option><option value="other">other</option>
          </select>
          <textarea class="form-control form-control-sm report-message mb-2" placeholder="Съобщение (по желание)"></textarea>
          <div class="d-flex gap-2 justify-content-end">
            <button class="btn btn-sm btn-outline-secondary" type="button" data-bs-toggle="collapse" data-bs-target="#${collapseId}">Отказ</button>
            <button class="btn btn-sm btn-outline-danger report-submit" type="button">Изпрати доклад</button>
          </div>
        </div>
      </div>`;
  }

  function votingHtml(type, id, score) {
    const isPost = type === 'post';
    const scoreId = isPost ? 'post-score' : `${type}-score-${id}`;
    return `
      <button class="vote-btn vote-btn--up" id="${type}-up-${id}" type="button" aria-label="Положителен вот">▲</button>
      <span id="${scoreId}" class="vote-score" ${isPost ? 'data-post-score' : ''}>${score}</span>
      <button class="vote-btn vote-btn--down" id="${type}-down-${id}" type="button" aria-label="Отрицателен вот">▼</button>
    `;
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
          <span>${formatRelativeTime(post.created_at)}</span>
          <span class="discussion-post-meta-separator">•</span>
          <span class="badge rounded-pill listing-pill subject-badge" style="${window.subjectBadgeUtils.getSubjectBadgeStyle(post.subject)}">${escapeHtml(post.subject.name)}</span>
        </div>
      </header>

      <p class="discussion-post-description mb-0">${escapeHtml(post.body)}</p>
      ${imgIf(post.image)}

      ${reportFormHtml('post', post.id)}

      <section class="mt-3">
        <h2 class="h6 text-muted mb-2">Автор</h2>
        ${authorCard(post.author, post.subject)}
      </section>
    </div></article>`;

    const voteWrap = document.getElementById(`post-vote-${post.id}`);
    voteWrap.innerHTML = votingHtml('post', post.id, post.score);
    const scoreEl = document.querySelector('[data-post-score]');
    document.getElementById(`post-up-${post.id}`).onclick = () => castVote(`/api/posts/${postId}/vote/`, scoreEl, 'post', 1, voteWrap, post.id);
    document.getElementById(`post-down-${post.id}`).onclick = () => castVote(`/api/posts/${postId}/vote/`, scoreEl, 'post', -1, voteWrap, post.id);
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
      ${reportFormHtml('comment', c.id)}
    </div></div>`).join('');

    items.forEach((c) => {
      const voteWrap = document.getElementById(`comment-vote-${c.id}`);
      if (voteWrap) voteWrap.innerHTML = votingHtml('comment', c.id, c.score);
    });

    commentsList.querySelectorAll('[id^="comment-up-"]').forEach((btn) => {
      const id = btn.id.replace('comment-up-', '');
      btn.onclick = () => castVote(`/api/comments/${id}/vote/`, document.getElementById(`comment-score-${id}`), 'comment', 1, document.getElementById(`comment-vote-${id}`), id);
    });
    commentsList.querySelectorAll('[id^="comment-down-"]').forEach((btn) => {
      const id = btn.id.replace('comment-down-', '');
      btn.onclick = () => castVote(`/api/comments/${id}/vote/`, document.getElementById(`comment-score-${id}`), 'comment', -1, document.getElementById(`comment-vote-${id}`), id);
    });
  }

  document.addEventListener('click', (event) => {
    if (!event.target.classList.contains('report-submit')) return;
    const wrap = event.target.closest('.discussion-report-box');
    if (!wrap) return;
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
