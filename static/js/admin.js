if (!guardRole(['admin'])) return;

const userList = document.getElementById('user-list');
const statsBox = document.getElementById('admin-stats');
const driverList = document.getElementById('driver-list');
const vehicleList = document.getElementById('vehicle-list');
const routeList = document.getElementById('route-list');

async function loadStats() {
  try {
    const stats = await api('/admin/stats');
    statsBox.innerHTML = `
      <div class="grid">
        <div class="card"><strong>Пользователи</strong><p>${stats.users}</p></div>
        <div class="card"><strong>Водители</strong><p>${stats.drivers}</p></div>
        <div class="card"><strong>Транспорт</strong><p>${stats.vehicles}</p></div>
        <div class="card"><strong>Маршруты</strong><p>${stats.routes}</p></div>
      </div>`;
  } catch (error) {
    statsBox.innerHTML = `<p class="muted">${error.message}</p>`;
    toast(error.message, true);
  }
}

async function loadUsers() {
  try {
    const users = await api('/auth/users');
    userList.innerHTML = formatList(
      users,
      (u) => `
        <div class="item">
          <div class="badge">${u.role}</div>
          <strong>${u.username}</strong><br>
          Создан: ${new Date(u.created_at).toLocaleString()}<br>
          <button data-user-id="${u.id}" class="secondary">Удалить</button>
        </div>
      `,
    );
  } catch (error) {
    userList.innerHTML = `<p class="muted">${error.message}</p>`;
  }
}

async function loadDrivers() {
  try {
    const drivers = await api('/drivers');
    driverList.innerHTML = formatList(
      drivers,
      (d) => `
        <div class="item">
          <strong>${d.first_name} ${d.last_name}</strong> (${d.license_number})<br>
          Пользователь: ${d.user_id}
        </div>
      `,
    );
  } catch (error) {
    driverList.innerHTML = `<p class="muted">${error.message}</p>`;
  }
}

async function loadVehicles() {
  try {
    const vehicles = await api('/vehicles');
    const driverOptions = await api('/drivers');
    vehicleList.innerHTML = formatList(
      vehicles,
      (v) => `
        <div class="item">
          <strong>${v.brand} ${v.model}</strong> (${v.reg_number})<br>
          Водитель: ${v.driver_id || 'не назначен'}
        </div>
      `,
    );

    const driverSelect = document.getElementById('assign-driver-id');
    const routeDriverSelect = document.getElementById('route_driver_id');
    driverSelect.innerHTML = driverOptions
      .map((d) => `<option value="${d.id}">${d.first_name} ${d.last_name}</option>`)
      .join('');
    routeDriverSelect.innerHTML = driverSelect.innerHTML;

    const vehicleSelect = document.getElementById('assign-vehicle-id');
    const routeVehicleSelect = document.getElementById('route_vehicle_id');
    vehicleSelect.innerHTML = vehicles
      .map((v) => `<option value="${v.id}">${v.brand} ${v.model} (${v.reg_number})</option>`)
      .join('');
    routeVehicleSelect.innerHTML = vehicleSelect.innerHTML;
  } catch (error) {
    vehicleList.innerHTML = `<p class="muted">${error.message}</p>`;
  }
}

async function loadRoutes() {
  try {
    const routes = await api('/routes');
    routeList.innerHTML = formatList(
      routes,
      (r) => `
        <div class="item">
          <strong>${r.start_location} → ${r.end_location}</strong><br>
          ${r.date} · ${r.distance} км · водитель ${r.driver_id}, транспорт ${r.vehicle_id}
        </div>
      `,
    );
  } catch (error) {
    routeList.innerHTML = `<p class="muted">${error.message}</p>`;
  }
}

async function handleUserCreate(event) {
  event.preventDefault();
  const form = event.target;
  const payload = {
    username: form.username.value.trim(),
    password: form.password.value,
    role: form.role.value,
  };

  if (payload.role === 'driver') {
    payload.driver = {
      first_name: form.first_name.value.trim(),
      last_name: form.last_name.value.trim(),
      license_number: form.license_number.value.trim(),
    };
  }

  try {
    await api('/auth/users', { method: 'POST', body: JSON.stringify(payload) });
    toast('Пользователь создан');
    form.reset();
    await loadUsers();
    await loadDrivers();
  } catch (error) {
    toast(error.message, true);
  }
}

async function handleUserDelete(event) {
  const button = event.target.closest('button[data-user-id]');
  if (!button) return;
  const id = button.getAttribute('data-user-id');
  try {
    await api(`/auth/users/${id}`, { method: 'DELETE' });
    toast('Пользователь удален');
    await loadUsers();
    await loadDrivers();
  } catch (error) {
    toast(error.message, true);
  }
}

async function handleDriverCreate(event) {
  event.preventDefault();
  const form = event.target;
  const payload = {
    first_name: form.d_first_name.value.trim(),
    last_name: form.d_last_name.value.trim(),
    license_number: form.d_license_number.value.trim(),
    user_id: Number(form.d_user_id.value),
  };
  try {
    await api('/drivers', { method: 'POST', body: JSON.stringify(payload) });
    toast('Водитель создан');
    form.reset();
    await loadDrivers();
    await loadVehicles();
  } catch (error) {
    toast(error.message, true);
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
    toast('Транспорт добавлен');
    form.reset();
    await loadVehicles();
  } catch (error) {
    toast(error.message, true);
  }
}

async function handleAssign(event) {
  event.preventDefault();
  const form = event.target;
  const vehicleId = Number(form.vehicle_id.value);
  const driverId = Number(form.driver_id.value);
  try {
    await api(`/vehicles/${vehicleId}/assign-driver`, {
      method: 'POST',
      body: JSON.stringify({ driver_id: driverId }),
    });
    toast('Водитель назначен');
    await loadVehicles();
  } catch (error) {
    toast(error.message, true);
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
    vehicle_id: Number(form.route_vehicle_id.value),
    driver_id: Number(form.route_driver_id.value),
  };
  try {
    await api('/routes', { method: 'POST', body: JSON.stringify(payload) });
    toast('Маршрут добавлен');
    form.reset();
    await loadRoutes();
  } catch (error) {
    toast(error.message, true);
  }
}

async function bootstrap() {
  await loadStats();
  await loadUsers();
  await loadDrivers();
  await loadVehicles();
  await loadRoutes();

  document.getElementById('create-user-form').addEventListener('submit', handleUserCreate);
  userList.addEventListener('click', handleUserDelete);
  document.getElementById('create-driver-form').addEventListener('submit', handleDriverCreate);
  document.getElementById('create-vehicle-form').addEventListener('submit', handleVehicleCreate);
  document.getElementById('assign-form').addEventListener('submit', handleAssign);
  document.getElementById('create-route-form').addEventListener('submit', handleRouteCreate);
  document.getElementById('logout-btn').addEventListener('click', logout);
}

bootstrap();
