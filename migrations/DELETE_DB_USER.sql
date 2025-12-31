-- 1. Terminate all connections to the database
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'comp_sci'
  AND pid <> pg_backend_pid();

-- 2. Drop the database itself
DROP DATABASE comp_sci;

-- 3. Drop user
DROP USER comp_sci_user;