(async function () {
  const meta = document.getElementById('post-page-meta');
  const postId = meta.dataset.postId;
  const appRoot = document.getElementById('app-root');
  const isAuthenticated = appRoot.dataset.authenticated === '1';
  const currentUserId = Number(appRoot.dataset.userId || 0);
  const loginUrl = appRoot.dataset.loginUrl;

  const postAlert = document.getElementById('post-alert');
  const postContainer = document.getElementById('post-container');
  const commentsList = document.getElementById('comments-list');
  let pendingDeleteCommentId = null;
  let currentPostSubject = null;

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

  function authorCard(author, subject, { showSubjectBadge = true } = {}) {
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
            ${showSubjectBadge ? `<span class="badge rounded-pill listing-pill subject-badge" style="${window.subjectBadgeUtils.getSubjectBadgeStyle(subject)}">${escapeHtml(subject.name)}</span>` : ''}
          </div>
        </div>
      </div>
    `;
  }

  function getImageUrl(payload) {
    if (!payload || typeof payload !== 'object') return '';

    if (typeof payload.image === 'string' && payload.image) {
      return payload.image;
    }

    if (Array.isArray(payload.images) && payload.images.length) {
      const first = payload.images[0];
      if (typeof first === 'string') return first;
      if (first && typeof first === 'object') {
        return first.image || first.image_url || first.url || first.src || '';
      }
    }

    return '';
  }

  function imgIf(payload) {
    const imageUrl = getImageUrl(payload);
    return imageUrl
      ? `<div class="discussion-image-frame marketplace-detail-image-frame rounded"><img src="${escapeHtml(imageUrl)}" class="discussion-image marketplace-detail-image" alt="Илюстрация към дискусия"></div>`
      : '';
  }

  function alertHtml(text, type = 'warning') { return `<div class="alert alert-${type}">${text}</div>`; }
  function loginAlert() { return `${alertHtml(`Трябва да сте логнати. <a href="${loginUrl}">Вход</a>`, 'warning')}`; }

  function animateSuccessAlert() {
    const successAlert = postAlert.querySelector('.alert-success');
    if (!successAlert) return;
    successAlert.classList.remove('alert-pop-highlight');
    void successAlert.offsetWidth;
    successAlert.classList.add('alert-pop-highlight');
  }

  function getNumber(value) {
    const num = Number(value);
    return Number.isFinite(num) ? num : 0;
  }

  function applyVoteUI(root, { score, userVote }) {
    const scoreEl = root.querySelector('.js-vote-score');
    const upBtn = root.querySelector('.js-vote-up');
    const downBtn = root.querySelector('.js-vote-down');
    const parsedUserVote = getNumber(userVote);

    if (scoreEl && score !== undefined) {
      scoreEl.textContent = String(score);
    }

    root.dataset.userVote = String(parsedUserVote);
    upBtn?.classList.toggle('is-active', parsedUserVote === 1);
    downBtn?.classList.toggle('is-active', parsedUserVote === -1);
  }

  function getVoteStateFromResponse(data) {
    return getNumber(data.vote_value ?? data.user_vote ?? data.vote ?? data.value ?? 0);
  }

  function getScoreFromResponse(data) {
    if (data.score !== undefined) return data.score;
    if (data.new_score !== undefined) return data.new_score;
    if (data.points !== undefined) return data.points;
    return undefined;
  }

  async function fetchFallbackScoreAndVote(root) {
    const targetType = root.dataset.type;
    const targetId = root.dataset.id;
    const detailUrl = targetType === 'post' ? `/api/posts/${targetId}/` : null;
    if (!detailUrl) return null;

    const res = await window.apiUtils.apiFetch(detailUrl);
    if (!res.ok) return null;

    const data = await res.json().catch(() => ({}));
    const score = getScoreFromResponse(data);
    return {
      score,
      userVote: getVoteStateFromResponse(data)
    };
  }

  async function handleVoteClick(root, direction) {
    if (!isAuthenticated) {
      postAlert.innerHTML = loginAlert();
      return;
    }

    const currentVote = getNumber(root.dataset.userVote);
    const nextVote = currentVote === direction ? 0 : direction;
    const targetType = root.dataset.type;
    const targetId = root.dataset.id;
    const voteUrl = targetType === 'post' ? `/api/posts/${targetId}/vote/` : `/api/comments/${targetId}/vote/`;

    try {
      const res = await window.apiUtils.apiFetch(voteUrl, {
        method: 'POST',
        body: JSON.stringify({ value: nextVote })
      });
      const data = await res.json().catch(() => ({}));

      if (res.status === 401 || res.status === 403) {
        postAlert.innerHTML = loginAlert();
        return;
      }

      if (!res.ok) {
        const msg = data.detail || data.non_field_errors?.[0] || 'Грешка при гласуване';
        postAlert.innerHTML = alertHtml(msg, 'danger');
        return;
      }

      const responseScore = getScoreFromResponse(data);
      let responseVote = getVoteStateFromResponse(data);

      if (data.vote_value === undefined && data.user_vote === undefined) {
        responseVote = nextVote;
      }

      if (responseScore === undefined) {
        const fallback = await fetchFallbackScoreAndVote(root);
        if (fallback) {
          applyVoteUI(root, fallback);
          return;
        }
      }

      applyVoteUI(root, {
        score: responseScore,
        userVote: responseVote
      });
      postAlert.innerHTML = '';
    } catch (error) {
      postAlert.innerHTML = alertHtml('Грешка при гласуване', 'danger');
    }
  }

  async function submitReport(targetType, targetId, reason, message, reportBox) {
    try {
      const res = await window.apiUtils.apiFetch('/api/reports/', {
        method: 'POST',
        body: JSON.stringify({ target_type: targetType, target_id: targetId, reason, message })
      });
      if (res.status === 401 || res.status === 403) {
        postAlert.innerHTML = loginAlert();
        return;
      }
      if (!res.ok) {
        postAlert.innerHTML = alertHtml('Неуспешно изпращане на репорта. Опитайте отново.', 'danger');
        return;
      }
      postAlert.innerHTML = alertHtml('Репортът ви е изпратен успешно.', 'success');
      animateSuccessAlert();
      const collapseEl = reportBox?.closest('.collapse');
      if (collapseEl) {
        bootstrap.Collapse.getOrCreateInstance(collapseEl).hide();
      }
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (error) {
      postAlert.innerHTML = alertHtml('Неуспешно изпращане на репорта. Опитайте отново.', 'danger');
    }
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
            <button class="btn btn-sm btn-outline-danger report-submit" type="button">Изпрати репорт</button>
          </div>
        </div>
      </div>`;
  }

  function votingHtml(type, id, score, userVote = 0) {
    return `
      <div class="js-vote" data-type="${type}" data-id="${id}" data-user-vote="${getNumber(userVote)}">
        <button class="vote-btn vote-btn--up js-vote-up" type="button" aria-label="Положителен вот">▲</button>
        <span class="vote-score js-vote-score">${getNumber(score)}</span>
        <button class="vote-btn vote-btn--down js-vote-down" type="button" aria-label="Отрицателен вот">▼</button>
      </div>
    `;
  }

  function commentCardHtml(comment) {
    const canDelete = Boolean(comment.can_delete)
      || (isAuthenticated && (Number(comment.author?.id) === currentUserId));
    const deleteBtn = canDelete
      ? `<button class="btn btn-sm btn-outline-danger discussion-comment-delete" type="button" data-comment-id="${comment.id}" aria-label="Изтрий коментара"><i class="bi bi-trash3" aria-hidden="true"></i></button>`
      : '';
    return `<div class="card discussion-comment-card" data-comment-id="${comment.id}"><div class="card-body">
      <section class="discussion-comment-content">
        <div class="discussion-comment-card-header">${deleteBtn}</div>
        ${authorCard(comment.author, currentPostSubject, { showSubjectBadge: false })}
        <p class="discussion-comment-body">${escapeHtml(comment.body)}</p>${imgIf(comment)}
        ${reportFormHtml('comment', comment.id)}
      </section>
    </div></div>`;
  }

  function ensureDeleteModal() {
    let modalEl = document.getElementById('comment-delete-modal');
    if (!modalEl) {
      modalEl = document.createElement('div');
      modalEl.className = 'modal fade';
      modalEl.id = 'comment-delete-modal';
      modalEl.tabIndex = -1;
      modalEl.setAttribute('aria-hidden', 'true');
      modalEl.innerHTML = `
        <div class="modal-dialog modal-dialog-centered">
          <div class="modal-content discussion-delete-modal-content">
            <div class="modal-body pb-0">
              <p class="mb-0">Сигурен ли си, че искаш да изтриеш коментара?</p>
            </div>
            <div class="modal-footer border-0">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Отказ</button>
              <button type="button" class="btn btn-danger" id="confirm-comment-delete">Изтрий</button>
            </div>
          </div>
        </div>`;
      document.body.appendChild(modalEl);
    }
    return modalEl;
  }

  async function deleteComment(commentId) {
    const res = await window.apiUtils.apiFetch(`/api/comments/${commentId}/`, { method: 'DELETE' });
    if (res.ok) {
      commentsList.querySelector(`[data-comment-id="${commentId}"]`)?.remove();
      if (!commentsList.querySelector('[data-comment-id]')) {
        commentsList.innerHTML = '<div class="alert alert-info">Няма резултати</div>';
      }
      return;
    }
    if (res.status === 401 || res.status === 403) {
      postAlert.innerHTML = alertHtml('Нямаш право да изтриеш този коментар.', 'danger');
      return;
    }
    if (res.status === 404) {
      postAlert.innerHTML = alertHtml('Коментарът не е намерен.', 'warning');
      return;
    }
    postAlert.innerHTML = alertHtml('Грешка при изтриване на коментар.', 'danger');
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
    currentPostSubject = post.subject;

    const postImage = imgIf(post);
    const postBodyContent = postImage
      ? `<div class="discussion-post-content row g-3 align-items-start">
          <div class="col-12 col-lg-7">
            <p class="discussion-post-description mb-0">${escapeHtml(post.body)}</p>
          </div>
          <div class="col-12 col-lg-5 discussion-post-image-col">
            ${postImage}
          </div>
        </div>`
      : `<p class="discussion-post-description mb-0">${escapeHtml(post.body)}</p>`;

    postContainer.innerHTML = `<article class="card discussion-post-card"><div class="card-body">
      <header class="discussion-post-header mb-3">
        <h1 class="h3 mb-2">${escapeHtml(post.title)}</h1>
        <div class="discussion-post-meta-row">
          <span>${formatRelativeTime(post.created_at)}</span>
          <span class="discussion-post-meta-separator">•</span>
          <span class="badge rounded-pill listing-pill subject-badge" style="${window.subjectBadgeUtils.getSubjectBadgeStyle(post.subject)}">${escapeHtml(post.subject.name)}</span>
        </div>
      </header>

      ${postBodyContent}

      ${reportFormHtml('post', post.id)}

      <section class="mt-3">
        <h2 class="h6 text-muted mb-2">Автор</h2>
        ${authorCard(post.author, post.subject)}
      </section>
    </div></article>`;

    const voteWrap = document.getElementById(`post-vote-${post.id}`);
    voteWrap.innerHTML = votingHtml('post', post.id, post.score, post.user_vote);
    const root = voteWrap.querySelector('.js-vote');
    if (root) {
      applyVoteUI(root, { score: post.score, userVote: post.user_vote });
    }

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
    commentsList.innerHTML = items.map((c) => commentCardHtml(c)).join('');

    items.forEach((c) => {
      const voteWrap = document.getElementById(`comment-vote-${c.id}`);
      if (!voteWrap) return;
      voteWrap.innerHTML = votingHtml('comment', c.id, c.score, c.user_vote);
      const root = voteWrap.querySelector('.js-vote');
      if (root) {
        applyVoteUI(root, { score: c.score, userVote: c.user_vote });
      }
    });

  }

  document.addEventListener('click', (event) => {
    const upBtn = event.target.closest('.js-vote-up');
    const downBtn = event.target.closest('.js-vote-down');
    if (upBtn || downBtn) {
      const root = event.target.closest('.js-vote');
      if (!root) return;
      handleVoteClick(root, upBtn ? 1 : -1);
      return;
    }

    const deleteBtn = event.target.closest('.discussion-comment-delete');
    if (deleteBtn) {
      pendingDeleteCommentId = deleteBtn.dataset.commentId;
      const modalEl = ensureDeleteModal();
      const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
      modal.show();
      return;
    }

    if (!event.target.classList.contains('report-submit')) return;
    const wrap = event.target.closest('.discussion-report-box');
    if (!wrap) return;
    const reasonEl = wrap.querySelector('.report-reason');
    const msgEl = wrap.querySelector('.report-message');
    submitReport(reasonEl.dataset.targetType, Number(reasonEl.dataset.targetId), reasonEl.value, msgEl.value, wrap);
  });

  const form = document.getElementById('comment-form');
  if (form) {
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const res = await window.apiUtils.apiFetch(`/api/posts/${postId}/comments/`, {
        method: 'POST',
        body: JSON.stringify({ body: document.getElementById('comment-body').value })
      });
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

  const modalEl = ensureDeleteModal();
  const confirmDeleteBtn = document.getElementById('confirm-comment-delete');
  confirmDeleteBtn?.addEventListener('click', async () => {
    if (!pendingDeleteCommentId) return;
    confirmDeleteBtn.disabled = true;
    try {
      await deleteComment(pendingDeleteCommentId);
      bootstrap.Modal.getOrCreateInstance(modalEl).hide();
    } catch (error) {
      postAlert.innerHTML = alertHtml('Грешка при изтриване на коментар.', 'danger');
    } finally {
      confirmDeleteBtn.disabled = false;
      pendingDeleteCommentId = null;
    }
  });

  await loadPost();
  await loadComments();
})();
