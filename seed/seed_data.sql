-- Auto-generated sample data for the training project
-- Users
INSERT INTO users (username, password, role, created_at, updated_at)
VALUES
    ('admin', 'pbkdf2:sha256:600000$2NbqdANoaXiQOtCJ3EejWw==$iDzVyxadC5QGizegESz2678/JBk6Hqk+EK2ptrnd+9E=', 'admin', NOW(), NOW()),
    ('manager', 'pbkdf2:sha256:600000$RZUvKth73an7puEHGG0JSg==$ounbFMrDDUpRGFLkaHzB9LNYlq8RBXMy6iA/WIb2P4s=', 'manager', NOW(), NOW()),
    ('driver_alex', 'pbkdf2:sha256:600000$E8CiZVEsX76KCXNtW1dCiw==$ZT2qHDgruwiSB8EU57S/q4c6qhTSUztxmCIlAMBuLZQ=', 'driver', NOW(), NOW()),
    ('driver_maria', 'pbkdf2:sha256:600000$LPmeyE7IXGuDW9kgeCsw1w==$VMlJEMDWJWdsJEdWoYNmzoFeFCgH3vSZy7BZ0PFBrAo=', 'driver', NOW(), NOW())
ON CONFLICT (username) DO NOTHING;

-- Drivers
INSERT INTO driver (first_name, last_name, license_number, user_id, created_at, updated_at)
SELECT 'Алексей', 'Иванов', 'DL-1001', id, NOW(), NOW() FROM users WHERE username = 'driver_alex'
ON CONFLICT (license_number) DO NOTHING;

INSERT INTO driver (first_name, last_name, license_number, user_id, created_at, updated_at)
SELECT 'Мария', 'Петрова', 'DL-1002', id, NOW(), NOW() FROM users WHERE username = 'driver_maria'
ON CONFLICT (license_number) DO NOTHING;

-- Vehicles
INSERT INTO vehicle (brand, model, reg_number, driver_id, created_at, updated_at)
VALUES
    ('Ford', 'Transit', 'A100AA', (SELECT id FROM driver WHERE license_number = 'DL-1001'), NOW(), NOW()),
    ('Mercedes', 'Sprinter', 'B200BB', (SELECT id FROM driver WHERE license_number = 'DL-1002'), NOW(), NOW()),
    ('GAZ', 'Gazelle Next', 'C300CC', NULL, NOW(), NOW())
ON CONFLICT (reg_number) DO NOTHING;

-- Routes
INSERT INTO route (start_location, end_location, date, distance, vehicle_id, driver_id, created_at, updated_at)
SELECT 'Склад', 'Магазин 1', CURRENT_DATE, 18.5,
       (SELECT id FROM vehicle WHERE reg_number = 'A100AA'),
       (SELECT id FROM driver WHERE license_number = 'DL-1001'),
       NOW(), NOW()
WHERE EXISTS (SELECT 1 FROM vehicle WHERE reg_number = 'A100AA')
  AND NOT EXISTS (
      SELECT 1 FROM route r
      WHERE r.start_location = 'Склад' AND r.end_location = 'Магазин 1' AND r.date = CURRENT_DATE
  );

INSERT INTO route (start_location, end_location, date, distance, vehicle_id, driver_id, created_at, updated_at)
SELECT 'Склад', 'Магазин 2', CURRENT_DATE + INTERVAL '1 day', 24.3,
       (SELECT id FROM vehicle WHERE reg_number = 'B200BB'),
       (SELECT id FROM driver WHERE license_number = 'DL-1002'),
       NOW(), NOW()
WHERE EXISTS (SELECT 1 FROM vehicle WHERE reg_number = 'B200BB')
  AND NOT EXISTS (
      SELECT 1 FROM route r
      WHERE r.start_location = 'Склад' AND r.end_location = 'Магазин 2' AND r.date = CURRENT_DATE + INTERVAL '1 day'
  );

-- Maintenance
INSERT INTO maintenance (type_of_work, cost, vehicle_id, created_at, updated_at)
SELECT 'ТО-1', 7500,
       (SELECT id FROM vehicle WHERE reg_number = 'A100AA'),
       NOW(), NOW()
WHERE EXISTS (SELECT 1 FROM vehicle WHERE reg_number = 'A100AA')
  AND NOT EXISTS (
      SELECT 1 FROM maintenance m
      JOIN vehicle v ON v.id = m.vehicle_id
      WHERE m.type_of_work = 'ТО-1' AND v.reg_number = 'A100AA'
  );

INSERT INTO maintenance (type_of_work, cost, vehicle_id, created_at, updated_at)
SELECT 'Замена масла', 3200,
       (SELECT id FROM vehicle WHERE reg_number = 'B200BB'),
       NOW(), NOW()
WHERE EXISTS (SELECT 1 FROM vehicle WHERE reg_number = 'B200BB')
  AND NOT EXISTS (
      SELECT 1 FROM maintenance m
      JOIN vehicle v ON v.id = m.vehicle_id
      WHERE m.type_of_work = 'Замена масла' AND v.reg_number = 'B200BB'
  );
