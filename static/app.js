const state = {
  token: localStorage.getItem('access_token') || '',
  role: localStorage.getItem('role') || '',
};

const toastEl = document.getElementById('toast');
const authInfo = document.getElementById('auth-info');
const profileData = document.getElementById('profile-data');
const vehiclesList = document.getElementById('vehicles-list');
const routesList = document.getElementById('routes-list');
const maintenanceList = document.getElementById('maintenance-list');
const driversList = document.getElementById('drivers-list');
const adminStats = document.getElementById('admin-stats');

function showToast(message, isError = false) {
  toastEl.textContent = message;
  toastEl.style.background = isError ? '#ef4444' : '#0ea5e9';
  toastEl.classList.add('show');
  setTimeout(() => toastEl.classList.remove('show'), 2500);
}

async function api(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (state.token) {
    headers.Authorization = `Bearer ${state.token}`;
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

function renderList(target, items, mapper) {
  if (!items?.length) {
    target.innerHTML = '<p class="muted">Нет данных</p>';
    return;
  }
  target.innerHTML = items.map(mapper).join('');
}

function renderInfo(target, obj) {
  target.textContent = JSON.stringify(obj, null, 2);
}

function setLoggedIn(token, role) {
  state.token = token;
  state.role = role;
  if (token) {
    localStorage.setItem('access_token', token);
  } else {
    localStorage.removeItem('access_token');
  }
  if (role) {
    localStorage.setItem('role', role);
  } else {
    localStorage.removeItem('role');
  }
  authInfo.textContent = token ? `Токен сохранен, роль: ${role}` : 'Не авторизованы';
}

async function handleLogin(event) {
  event.preventDefault();
  const form = event.target;
  const payload = {
    username: form.username.value.trim(),
    password: form.password.value,
  };
  try {
    const data = await api('/auth/login', { method: 'POST', body: JSON.stringify(payload) });
    setLoggedIn(data.access_token, data.role);
    showToast('Вход выполнен');
    await refreshAll();
  } catch (error) {
    showToast(error.message, true);
  }
}

function handleLogout() {
  setLoggedIn('', '');
  profileData.textContent = '';
  vehiclesList.textContent = '';
  routesList.textContent = '';
  maintenanceList.textContent = '';
  driversList.textContent = '';
  adminStats.textContent = '';
  showToast('Токен очищен');
}

async function loadProfile() {
  try {
    const data = await api('/auth/me');
    renderInfo(profileData, data);
  } catch (error) {
    renderInfo(profileData, { error: error.message });
    showToast(error.message, true);
  }
}

async function loadVehicles() {
  try {
    const data = await api('/vehicles');
    renderList(
      vehiclesList,
      data,
      (vehicle) => `
        <div class="item">
          <strong>#${vehicle.id}</strong> ${vehicle.brand} ${vehicle.model} (${vehicle.reg_number})<br>
          Водитель: ${vehicle.driver_id ?? 'не назначен'}
        </div>
      `,
    );
  } catch (error) {
    renderInfo(vehiclesList, { error: error.message });
    showToast(error.message, true);
  }
}

async function loadRoutes() {
  try {
    const data = await api('/routes');
    renderList(
      routesList,
      data,
      (route) => `
        <div class="item">
          <strong>#${route.id}</strong> ${route.start_location} → ${route.end_location}<br>
          ${route.date} · ${route.distance} км · транспорт ${route.vehicle_id}, водитель ${route.driver_id}
        </div>
      `,
    );
  } catch (error) {
    renderInfo(routesList, { error: error.message });
    showToast(error.message, true);
  }
}

async function loadMaintenance() {
  try {
    const data = await api('/maintenance');
    renderList(
      maintenanceList,
      data,
      (item) => `
        <div class="item">
          <strong>#${item.id}</strong> ${item.type_of_work}<br>
          Транспорт ${item.vehicle_id} · ${item.cost}₽
        </div>
      `,
    );
  } catch (error) {
    renderInfo(maintenanceList, { error: error.message });
    showToast(error.message, true);
  }
}

async function loadDrivers() {
  try {
    const data = await api('/drivers');
    renderList(
      driversList,
      data,
      (driver) => `
        <div class="item">
          <strong>#${driver.id}</strong> ${driver.first_name} ${driver.last_name}<br>
          Права: ${driver.license_number} · Пользователь ${driver.user_id}
        </div>
      `,
    );
  } catch (error) {
    renderInfo(driversList, { error: error.message });
    showToast(error.message, true);
  }
}

async function loadAdminStats() {
  if (state.role !== 'admin') {
    adminStats.textContent = 'Доступ только для администратора';
    return;
  }
  try {
    const data = await api('/admin/stats');
    renderInfo(adminStats, data);
  } catch (error) {
    renderInfo(adminStats, { error: error.message });
    showToast(error.message, true);
  }
}

async function handleVehicleCreate(event) {
  event.preventDefault();
  const form = event.target;
  const payload = {
    brand: form.brand.value.trim(),
    model: form.model.value.trim(),
    reg_number: form.reg_number.value.trim(),
  };
  try {
    await api('/vehicles', { method: 'POST', body: JSON.stringify(payload) });
    form.reset();
    showToast('Транспорт добавлен');
    await loadVehicles();
  } catch (error) {
    showToast(error.message, true);
  }
}

async function handleRouteCreate(event) {
  event.preventDefault();
  const form = event.target;
  const payload = {
    start_location: form.start_location.value.trim(),
    end_location: form.end_location.value.trim(),
    date: form.date.value,
    distance: form.distance.value,
    vehicle_id: Number(form.vehicle_id.value),
    driver_id: form.driver_id.value ? Number(form.driver_id.value) : undefined,
  };
  try {
    await api('/routes', { method: 'POST', body: JSON.stringify(payload) });
    form.reset();
    showToast('Маршрут создан');
    await loadRoutes();
  } catch (error) {
    showToast(error.message, true);
  }
}

async function handleMaintenanceCreate(event) {
  event.preventDefault();
  const form = event.target;
  const payload = {
    type_of_work: form.type_of_work.value.trim(),
    cost: Number(form.cost.value),
    vehicle_id: Number(form.vehicle_id.value),
  };
  try {
    await api('/maintenance', { method: 'POST', body: JSON.stringify(payload) });
    form.reset();
    showToast('Запись сохранена');
    await loadMaintenance();
  } catch (error) {
    showToast(error.message, true);
  }
}

async function handleDriverCreate(event) {
  event.preventDefault();
  const form = event.target;
  const payload = {
    first_name: form.first_name.value.trim(),
    last_name: form.last_name.value.trim(),
    license_number: form.license_number.value.trim(),
    user_id: Number(form.user_id.value),
  };
  try {
    await api('/drivers', { method: 'POST', body: JSON.stringify(payload) });
    form.reset();
    showToast('Водитель добавлен');
    await loadDrivers();
  } catch (error) {
    showToast(error.message, true);
  }
}

async function refreshAll() {
  await Promise.allSettled([
    loadProfile(),
    loadVehicles(),
    loadRoutes(),
    loadMaintenance(),
    loadDrivers(),
    loadAdminStats(),
  ]);
}

function bindEvents() {
  document.getElementById('login-form').addEventListener('submit', handleLogin);
  document.getElementById('logout-btn').addEventListener('click', handleLogout);
  document.getElementById('refresh-profile').addEventListener('click', loadProfile);
  document.getElementById('load-vehicles').addEventListener('click', loadVehicles);
  document.getElementById('vehicle-form').addEventListener('submit', handleVehicleCreate);
  document.getElementById('load-routes').addEventListener('click', loadRoutes);
  document.getElementById('route-form').addEventListener('submit', handleRouteCreate);
  document.getElementById('load-maintenance').addEventListener('click', loadMaintenance);
  document.getElementById('maintenance-form').addEventListener('submit', handleMaintenanceCreate);
  document.getElementById('load-drivers').addEventListener('click', loadDrivers);
  document.getElementById('driver-form').addEventListener('submit', handleDriverCreate);
  document.getElementById('load-admin').addEventListener('click', loadAdminStats);
}

function init() {
  bindEvents();
  if (state.token) {
    authInfo.textContent = `Токен найден, роль: ${state.role || 'неизвестна'}`;
    refreshAll();
  } else {
    authInfo.textContent = 'Не авторизованы';
  }
}

init();
