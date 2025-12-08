if (!guardRole(['manager'])) return;

const driverList = document.getElementById('manager-driver-list');
const vehicleList = document.getElementById('manager-vehicle-list');
const routeList = document.getElementById('manager-route-list');
const maintenanceList = document.getElementById('manager-maintenance-list');

async function loadDrivers() {
  try {
    const drivers = await api('/drivers');
    driverList.innerHTML = formatList(
      drivers,
      (d) => `
        <div class="item">
          <strong>${d.first_name} ${d.last_name}</strong><br>
          Права: ${d.license_number} · Пользователь ${d.user_id}
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
    vehicleList.innerHTML = formatList(
      vehicles,
      (v) => `
        <div class="item">
          <strong>${v.brand} ${v.model}</strong> (${v.reg_number})<br>
          Водитель: ${v.driver_id || 'не назначен'}
        </div>
      `,
    );
    const vehicleSelect = document.getElementById('mgr-vehicle-id');
    const assignVehicleSelect = document.getElementById('assign-vehicle-id');
    const maintenanceVehicleSelect = document.getElementById('maintenance-vehicle');
    const options = vehicles.map((v) => `<option value="${v.id}">${v.brand} ${v.model} (${v.reg_number})</option>`).join('');
    vehicleSelect.innerHTML = options;
    assignVehicleSelect.innerHTML = options;
    maintenanceVehicleSelect.innerHTML = options;
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

async function loadMaintenance() {
  try {
    const maintenance = await api('/maintenance');
    maintenanceList.innerHTML = formatList(
      maintenance,
      (m) => `
        <div class="item">
          <strong>${m.type_of_work}</strong> · ${m.cost} ₽<br>
          Транспорт: ${m.vehicle_id}
        </div>
      `,
    );
  } catch (error) {
    maintenanceList.innerHTML = `<p class="muted">${error.message}</p>`;
  }
}

async function loadDriverSelects() {
  const drivers = await api('/drivers');
  const routeDriverSelect = document.getElementById('mgr-route-driver-id');
  const assignDriverSelect = document.getElementById('mgr-assign-driver-id');
  const options = drivers.map((d) => `<option value="${d.id}">${d.first_name} ${d.last_name}</option>`).join('');
  routeDriverSelect.innerHTML = options;
  assignDriverSelect.innerHTML = options;
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
    driver_id: Number(form.driver_id.value),
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
    toast('Обслуживание добавлено');
    form.reset();
    await loadMaintenance();
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
    await api(`/vehicles/${vehicleId}/assign-driver`, { method: 'POST', body: JSON.stringify({ driver_id: driverId }) });
    toast('Водитель назначен');
    await loadVehicles();
  } catch (error) {
    toast(error.message, true);
  }
}

async function bootstrap() {
  await Promise.all([loadDrivers(), loadVehicles(), loadRoutes(), loadMaintenance(), loadDriverSelects()]);
  document.getElementById('route-form').addEventListener('submit', handleRouteCreate);
  document.getElementById('maintenance-form').addEventListener('submit', handleMaintenanceCreate);
  document.getElementById('assign-form').addEventListener('submit', handleAssign);
  document.getElementById('logout-btn').addEventListener('click', logout);
}

bootstrap();
