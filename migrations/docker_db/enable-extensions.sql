-- pgvector extension (should already be available in the image)
CREATE EXTENSION IF NOT EXISTS vector;

-- Apache AGE extension
CREATE EXTENSION IF NOT EXISTS age;

-- Load AGE’s shared library and set search_path so cypher() is in scope
LOAD 'age';
SET search_path = ag_catalog, "$user", public;