## start docker:

`docker compose up -d`

## Connect to DB directly:

```
docker exec -it pgvector-db psql -U postgres -d vector_test
```