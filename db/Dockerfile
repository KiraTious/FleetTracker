FROM postgres:17

# Allow overriding creds/db name at runtime; defaults align with docker-compose
ENV POSTGRES_USER=postgres \
    POSTGRES_PASSWORD=postgres \
    POSTGRES_DB=fleettracker

# Base schema and seed data will be applied automatically on first container start
COPY db/schema.sql /docker-entrypoint-initdb.d/00_schema.sql
COPY seed/seed_data.sql /docker-entrypoint-initdb.d/10_seed_data.sql
