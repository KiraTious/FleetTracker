const session = {
  token: localStorage.getItem('access_token') || '',
  role: localStorage.getItem('role') || '',
};

function setSession(token, role) {
  session.token = token || '';
  session.role = role || '';
  if (session.token) {
    localStorage.setItem('access_token', session.token);
  } else {
    localStorage.removeItem('access_token');
  }
  if (session.role) {
    localStorage.setItem('role', session.role);
  } else {
    localStorage.removeItem('role');
  }
}

function logout() {
  setSession('', '');
  window.location.href = '/login';
}

async function api(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (session.token) {
    headers.Authorization = `Bearer ${session.token}`;
  }
  const response = await fetch(path, { ...options, headers });
  const contentType = response.headers.get('content-type') || '';
  const data = contentType.includes('application/json') ? await response.json() : await response.text();
  if (!response.ok) {
    const message = data?.message || response.statusText;
    throw new Error(message);
  }
  return data;
}

function toast(message, isError = false) {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = message;
  el.style.background = isError ? '#ef4444' : '#0ea5e9';
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), 2600);
}

async function loadCurrentUser() {
  const me = await api('/auth/me');
  return me;
}

function guardRole(allowedRoles) {
  if (!session.token) {
    window.location.href = '/login';
    return false;
  }
  if (allowedRoles && !allowedRoles.includes(session.role)) {
    const target = session.role ? `/portal/${session.role}` : '/login';
    window.location.href = target;
    return false;
  }
  return true;
}

function formatList(items, mapper, emptyText = 'Нет данных') {
  if (!items?.length) return `<p class="muted">${emptyText}</p>`;
  return items.map(mapper).join('');
}
