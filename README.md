# SITRA Viewer

Containerized React and FastAPI scaffold for the National Archives' Situation Report Army records (NAID 604416). Source details are in [docs/nara-source.md](docs/nara-source.md).

## Run

Requires Docker Compose.

Copy `.env.example` to `.env` to override the local Neo4j connection defaults.

```sh
docker compose up --build
```

Open <http://localhost:8080>. The API health endpoint is proxied at <http://localhost:8080/api/health>; Neo4j Browser is at <http://localhost:7474>. Neo4j runs locally without authentication and stores data in a persistent Docker volume.

For hot-reload development, run:

```sh
docker compose -f compose.yaml -f compose.dev.yaml up --build
```

Open <http://localhost:8080> for the frontend in development mode too.

## Import command

Put the selected NARA data file in `data/`. Run the importer separately from app startup:

```sh
docker compose run --rm backend uv run --no-sync python -m app.import_data --source /data/sitra-source-file
```

Replace `sitra-source-file` with the file's name in `data/`. The command entry point is scaffolded in Phase 1; parsing and loading are scheduled for Phase 3.
