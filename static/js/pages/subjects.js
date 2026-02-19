(async function () {
  const meta = document.getElementById('subjects-page-meta');
  const slug = meta.dataset.subjectSlug;
  const list = document.getElementById('posts-list');
  const alertBox = document.getElementById('posts-alert');
  const PAGE_SIZE = 10;
  let currentUrl = null;

  function getAuthorInitial(author) {
    const label = author.display_name || author.username || '?';
    return label.charAt(0).toUpperCase();
  }

  function escapeHtml(value) {
    return String(value ?? '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('\"', '&quot;')
      .replaceAll("'", '&#39;');
  }

  function roleBadge(author) {
    if (!author.role) return '';
    const roleClass = author.role === 'teacher' ? 'role-badge--teacher' : 'role-badge--learner';
    const roleLabel = author.role_label || (author.role === 'teacher' ? 'Учител' : 'Учащ');
    return `<span class="badge rounded-pill listing-pill role-badge ${roleClass}">${escapeHtml(roleLabel)}</span>`;
  }

  function subjectBadge(post, isGlobalFeed) {
    if (!isGlobalFeed || !post.subject) return '';
    return `<span class="badge rounded-pill listing-pill subject-badge" style="${window.subjectBadgeUtils.getSubjectBadgeStyle(post.subject)}">${escapeHtml(post.subject.name)}</span>`;
  }

  function authorMeta(post, isGlobalFeed) {
    return `
      <div class="discussion-author-row d-flex align-items-center justify-content-between gap-2 flex-wrap">
        <div class="d-flex align-items-center gap-2 flex-wrap">
          <span class="discussion-author-avatar" aria-hidden="true">${getAuthorInitial(post.author)}</span>
          <span class="discussion-author-text">${escapeHtml(post.author.username)} • Ниво ${escapeHtml(post.author.level)}</span>
          <div class="d-flex flex-wrap gap-2 align-items-center">
            ${subjectBadge(post, isGlobalFeed)}
            ${roleBadge(post.author)}
          </div>
        </div>
      </div>`;
  }

  function showAlert(text, type = 'warning') {
    alertBox.innerHTML = `<div class="alert alert-${type}">${text}</div>`;
  }

  function render(posts) {
    const isGlobalFeed = slug === 'all';
    if (!posts.length) {
      list.innerHTML = '<div class="alert alert-info">Няма резултати</div>';
      return;
    }

    list.innerHTML = posts.map((post) => `
      <article class="discussion-card">
        <div class="discussion-main">
          <h2 class="discussion-title mb-2">${escapeHtml(post.title)}</h2>
          <p class="discussion-snippet mb-2">${escapeHtml(post.excerpt)}</p>
          ${authorMeta(post, isGlobalFeed)}
        </div>
        <div class="discussion-side">
          <span class="discussion-points-pill">${post.score} точки</span>
        </div>
        <a href="/posts/${post.id}/" class="stretched-link discussion-card-link" aria-label="Отвори дискусията: ${escapeHtml(post.title)}"></a>
      </article>`).join('');
  }

  async function load(url) {
    alertBox.innerHTML = '';
    const res = await window.apiUtils.apiFetch(url);
    if (res.status === 404) {
      showAlert('Не е намерено');
      list.innerHTML = '';
      return;
    }
    if (res.status === 400) {
      showAlert('Невалидна заявка');
      return;
    }
    const data = await res.json();
    currentUrl = url;
    render(data.results || []);
    window.zpPagination.render({
      containerId: 'posts-pagination',
      count: data.count,
      pageSize: PAGE_SIZE,
      currentUrl,
      onPageChange: (page) => load(window.zpPagination.updatePageInUrl(currentUrl, page)),
    });
  }

  function buildUrl() {
    const sort = document.getElementById('sort-select').value;
    const q = encodeURIComponent(document.getElementById('search-input').value.trim());
    let url = `/api/posts/?subject=${encodeURIComponent(slug)}&sort=${sort}&page=1`;
    if (q) url += `&q=${q}`;
    return url;
  }

  document.getElementById('search-btn').addEventListener('click', () => load(buildUrl()));
  document.getElementById('sort-select').addEventListener('change', () => load(buildUrl()));

  load(buildUrl());
})();
