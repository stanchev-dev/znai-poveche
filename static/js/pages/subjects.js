(async function () {
  const meta = document.getElementById('subjects-page-meta');
  const slug = meta.dataset.subjectSlug;
  const list = document.getElementById('posts-list');
  const alertBox = document.getElementById('posts-alert');
  let nextUrl = null;
  let prevUrl = null;

  function authorChip(author) {
    return `<span class="badge bg-light text-dark">${author.username} (${author.display_name}, ниво ${author.level})</span>`;
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
      <div class="card"><div class="card-body">
        <h2 class="h5">${post.title}</h2>
        <p>${post.excerpt}</p>
        <p class="mb-1">Точки: <strong>${post.score}</strong></p>
        ${authorChip(post.author)}
        <div class="mt-2"><a href="/posts/${post.id}/" class="btn btn-sm btn-primary">Прочети</a></div>
      </div></div>`).join('');
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
    nextUrl = data.next;
    prevUrl = data.previous;
    render(data.results || []);
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
  document.getElementById('prev-btn').addEventListener('click', () => { if (prevUrl) load(prevUrl); });
  document.getElementById('next-btn').addEventListener('click', () => { if (nextUrl) load(nextUrl); });

  load(buildUrl());
})();
