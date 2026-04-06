-- Выполнить в pgAdmin: Query Tool, под суперпользователем postgres.
-- Потом в .env:
--   DATABASE_URL=postgresql+asyncpg://vpn:vpn@localhost:5432/vpn

CREATE USER vpn WITH PASSWORD 'vpn';

CREATE DATABASE vpn OWNER vpn;

GRANT ALL PRIVILEGES ON DATABASE vpn TO vpn;

-- На PostgreSQL 15+ для схемы public иногда нужно (после подключения к БД vpn):
-- \c vpn
-- GRANT ALL ON SCHEMA public TO vpn;
