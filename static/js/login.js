async function handleLogin(event) {
  event.preventDefault();
  const form = event.target;
  const payload = {
    username: form.username.value.trim(),
    password: form.password.value,
  };
  try {
    const data = await api('/auth/login', { method: 'POST', body: JSON.stringify(payload) });
    setSession(data.access_token, data.role);
    toast('Вход выполнен');
    const target = `/portal/${data.role}`;
    window.location.href = target;
  } catch (error) {
    toast(error.message, true);
  }
}

document.getElementById('login-form').addEventListener('submit', handleLogin);

if (session.token && session.role) {
  window.location.href = `/portal/${session.role}`;
}
