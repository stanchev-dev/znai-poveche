(function () {
  function parsePageFromUrl(url) {
    if (!url) return 1;
    const parsed = new URL(url, window.location.origin);
    const page = Number(parsed.searchParams.get('page') || '1');
    return Number.isFinite(page) && page > 0 ? page : 1;
  }

  function createRange(start, end) {
    const values = [];
    for (let page = start; page <= end; page += 1) {
      values.push(page);
    }
    return values;
  }

  function getPageItems(currentPage, totalPages) {
    if (totalPages <= 1) return [1];
    if (totalPages <= 5) return createRange(1, totalPages);

    const pages = new Set([1, totalPages, currentPage - 1, currentPage, currentPage + 1]);
    const normalized = [...pages]
      .filter((page) => page >= 1 && page <= totalPages)
      .sort((a, b) => a - b);

    const items = [];
    normalized.forEach((page, index) => {
      if (index > 0 && page - normalized[index - 1] > 1) {
        items.push('ellipsis');
      }
      items.push(page);
    });
    return items;
  }

  function render({
    containerId,
    count,
    pageSize,
    currentUrl,
    onPageChange,
  }) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const totalPages = Math.max(1, Math.ceil((Number(count) || 0) / pageSize));
    const currentPage = Math.min(parsePageFromUrl(currentUrl), totalPages);
    const items = getPageItems(currentPage, totalPages);

    function addPageButton({ page, label, ariaLabel, isCurrent = false }) {
      const li = document.createElement('li');
      li.className = `page-item${isCurrent ? ' active' : ''}`;

      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'page-link';
      button.textContent = label;
      if (ariaLabel) button.setAttribute('aria-label', ariaLabel);
      if (isCurrent) {
        button.setAttribute('aria-current', 'page');
      } else {
        button.addEventListener('click', () => onPageChange(page));
      }

      li.appendChild(button);
      container.appendChild(li);
    }

    function addEllipsis() {
      const li = document.createElement('li');
      li.className = 'page-item disabled';
      li.setAttribute('aria-hidden', 'true');

      const span = document.createElement('span');
      span.className = 'page-link';
      span.textContent = '…';
      li.appendChild(span);
      container.appendChild(li);
    }

    container.innerHTML = '';

    if (totalPages > 1 && currentPage > 1) {
      addPageButton({
        page: currentPage - 1,
        label: '‹',
        ariaLabel: 'Предишна страница',
      });
    }

    items.forEach((item) => {
      if (item === 'ellipsis') {
        addEllipsis();
        return;
      }

      addPageButton({
        page: item,
        label: String(item),
        isCurrent: item === currentPage,
      });
    });

    if (totalPages > 1 && currentPage < totalPages) {
      addPageButton({
        page: currentPage + 1,
        label: '›',
        ariaLabel: 'Следваща страница',
      });
    }
  }

  function updatePageInUrl(url, page) {
    const parsed = new URL(url, window.location.origin);
    parsed.searchParams.set('page', String(page));
    return `${parsed.pathname}${parsed.search}`;
  }

  window.zpPagination = {
    parsePageFromUrl,
    render,
    updatePageInUrl,
  };
})();
