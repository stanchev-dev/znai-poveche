(function () {
  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
      return parts.pop().split(';').shift();
    }
    return null;
  }

  async function apiFetch(url, options = {}) {
    const config = { ...options, credentials: 'same-origin' };
    const method = (config.method || 'GET').toUpperCase();
    const headers = new Headers(config.headers || {});
    const csrf = getCookie('csrftoken');

    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method) && csrf) {
      headers.set('X-CSRFToken', csrf);
    }

    if (config.body && !(config.body instanceof FormData) && !headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }

    config.headers = headers;
    return fetch(url, config);
  }

  window.apiUtils = { getCookie, apiFetch };
})();
