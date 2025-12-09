-- TEST Vector DB
CREATE TABLE IF NOT EXISTS items (
  id bigserial PRIMARY KEY,
  embedding vector(3)
);

INSERT INTO items (embedding) VALUES ('[1,2,3]'), ('[4,5,6]');

SELECT * FROM items
ORDER BY embedding <-> '[3,1,2]'
LIMIT 5;


-- TEST Graph DB
SELECT create_graph('test_graph');

-- Simple graph write + read
SELECT *
FROM cypher('test_graph', $$
  CREATE (n:Person {name: 'Alice'})-[:KNOWS]->(m:Person {name: 'Bob'})
  RETURN n, m
$$) AS (n agtype, m agtype);