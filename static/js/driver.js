if (!guardRole(['driver'])) return;

const profileBox = document.getElementById('driver-profile');
const vehicleBox = document.getElementById('driver-vehicle');
const maintenanceBox = document.getElementById('driver-maintenance');
const routesBox = document.getElementById('driver-routes');

async function loadProfile() {
  try {
    const me = await loadCurrentUser();
    profileBox.innerHTML = `
      <p><strong>Логин:</strong> ${me.username}</p>
      <p><strong>Роль:</strong> ${me.role}</p>
      ${me.driver ? `<p><strong>Водитель:</strong> ${me.driver.first_name} ${me.driver.last_name}</p>` : ''}
    `;
  } catch (error) {
    profileBox.innerHTML = `<p class="muted">${error.message}</p>`;
  }
}

async function loadVehicles() {
  try {
    const vehicles = await api('/vehicles');
    vehicleBox.innerHTML = formatList(
      vehicles,
      (v) => `
        <div class="item">
          <strong>${v.brand} ${v.model}</strong> (${v.reg_number})
        </div>
      `,
      'За вами не закреплено транспорта',
    );
  } catch (error) {
    vehicleBox.innerHTML = `<p class="muted">${error.message}</p>`;
  }
}

async function loadMaintenance() {
  try {
    const maintenance = await api('/maintenance');
    maintenanceBox.innerHTML = formatList(
      maintenance,
      (m) => `
        <div class="item">
          <strong>${m.type_of_work}</strong> · ${m.cost} ₽
        </div>
      `,
      'Нет записей по обслуживанию',
    );
  } catch (error) {
    maintenanceBox.innerHTML = `<p class="muted">${error.message}</p>`;
  }
}

async function loadRoutes() {
  try {
    const routes = await api('/routes');
    const today = new Date().toISOString().slice(0, 10);
    const todays = routes.filter((r) => r.date.startsWith(today));
    routesBox.innerHTML = `
      <div class="card">
        <h3>Маршруты на сегодня</h3>
        ${formatList(
          todays,
          (r) => `<div class="item">${r.start_location} → ${r.end_location} · ${r.distance} км</div>`,
          'Сегодняшний маршрут не назначен',
        )}
      </div>
      <div class="card">
        <h3>Все маршруты</h3>
        ${formatList(
          routes,
          (r) => `<div class="item">${r.date}: ${r.start_location} → ${r.end_location} (${r.distance} км)</div>`,
          'История маршрутов пуста',
        )}
      </div>
    `;
  } catch (error) {
    routesBox.innerHTML = `<p class="muted">${error.message}</p>`;
  }
}

async function bootstrap() {
  await Promise.all([loadProfile(), loadVehicles(), loadMaintenance(), loadRoutes()]);
  document.getElementById('logout-btn').addEventListener('click', logout);
}

bootstrap();
