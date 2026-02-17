(async function () {
  const scopeSelect = document.getElementById('scope-select');
  const subjectWrap = document.getElementById('subject-wrap');
  const subjectSelect = document.getElementById('subject-select');
  const tbody = document.getElementById('leaderboard-body');
  const alertBox = document.getElementById('leaderboard-alert');
  const subjectScoreHead = document.getElementById('subject-score-head');
  const PAGE_SIZE = 20;
  let currentUrl = null;

  async function loadSubjects() {
    const res = await window.apiUtils.apiFetch('/api/subjects/');
    if (!res.ok) return;
    const subjects = await res.json();
    subjectSelect.innerHTML = subjects.map((s) => `<option value="${s.slug}">${s.name}</option>`).join('');
  }

  function buildUrl() {
    if (scopeSelect.value === 'subject') {
      return `/api/leaderboard/?scope=subject&subject=${encodeURIComponent(subjectSelect.value)}&page=1`;
    }
    return '/api/leaderboard/?scope=global&page=1';
  }

  async function load(url) {
    alertBox.innerHTML = '';
    const res = await window.apiUtils.apiFetch(url);
    if (res.status === 404) {
      alertBox.innerHTML = '<div class="alert alert-warning">Не е намерено</div>';
      tbody.innerHTML = '';
      return;
    }
    if (res.status === 400) {
      alertBox.innerHTML = '<div class="alert alert-warning">Невалидна заявка</div>';
      return;
    }
    const data = await res.json();
    currentUrl = url;
    const subjectMode = data.scope === 'subject';
    subjectScoreHead.style.display = subjectMode ? '' : 'none';

    if (!data.results.length) {
      tbody.innerHTML = '<tr><td colspan="5">Няма резултати</td></tr>';
    } else {
      tbody.innerHTML = data.results.map((r) => `<tr>
        <td>${r.rank}</td>
        <td>${r.username} (${r.display_name})</td>
        <td>${r.level}</td>
        <td>${r.reputation_points}</td>
        <td style="display:${subjectMode ? '' : 'none'}">${subjectMode ? r.subject_score : ''}</td>
      </tr>`).join('');
    }

    window.zpPagination.render({
      containerId: 'leaderboard-pagination',
      count: data.count,
      pageSize: PAGE_SIZE,
      currentUrl,
      onPageChange: (page) => load(window.zpPagination.updatePageInUrl(currentUrl, page)),
    });
  }

  scopeSelect.addEventListener('change', () => {
    const isSubject = scopeSelect.value === 'subject';
    subjectWrap.style.display = isSubject ? '' : 'none';
    load(buildUrl());
  });
  subjectSelect.addEventListener('change', () => load(buildUrl()));

  await loadSubjects();
  await load(buildUrl());
})();
