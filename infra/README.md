# Infrastructure

Local infrastructure is intentionally small.

## Default

- Postgres with pgvector
- Temporal
- Temporal UI

Start:

```sh
make infra-up
```

## Future Profiles

Optional services are behind the `future` profile:

```sh
docker compose --profile future up -d qdrant nats
```

Keep future services optional until the MVP memory PR loop needs them.
