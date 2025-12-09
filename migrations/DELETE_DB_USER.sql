-- 1. Terminate all connections to the database
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'psych_rag_test_removal'
  AND pid <> pg_backend_pid();

-- 2. Drop the database itself
DROP DATABASE psych_rag_test_removal;

-- 3. Drop user
DROP USER psych_rag_app_user_test_removal;