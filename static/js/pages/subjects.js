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

  function authorMeta(author) {
    return `
      <div class="discussion-author-meta">
        <span class="discussion-author-avatar" aria-hidden="true">${getAuthorInitial(author)}</span>
        <span class="discussion-author-text">${author.username} • Ниво ${author.level}</span>
      </div>`;
  }

  function showAlert(text, type = 'warning') {
    alertBox.innerHTML = `<div class="alert alert-${type}">${text}</div>`;
  }

  function render(posts) {
    if (!posts.length) {
      list.innerHTML = '<div class="alert alert-info">Няма резултати</div>';
      return;
    }

    list.innerHTML = posts.map((post) => `
      <article class="discussion-card">
        <span class="discussion-accent" aria-hidden="true"></span>
        <div class="discussion-main">
          <h2 class="discussion-title mb-2">${post.title}</h2>
          <p class="discussion-snippet mb-2">${post.excerpt}</p>
          ${authorMeta(post.author)}
        </div>
        <div class="discussion-side">
          <span class="discussion-points-pill">${post.score} точки</span>
          <a href="/posts/${post.id}/" class="btn btn-sm btn-brand-outline">Прочети →</a>
        </div>
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
