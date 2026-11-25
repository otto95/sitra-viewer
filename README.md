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

Run backend unit and Neo4j integration tests with:

```sh
docker compose -f compose.yaml -f compose.dev.yaml exec backend uv run --no-sync pytest
```

## Import command

Download one or more ASCII translations from NARA's [SITRA series](https://catalog.archives.gov/id/604416) into `data/`. The four files cover 1966–1973. Run the importer separately from app startup:

```sh
docker compose run --rm backend uv run --no-sync python -m app.import_data \
  --source /data/SITRA.TR.6668.txt \
  --source /data/SITRA.TR.69.txt \
  --source /data/SITRA.TR.70.txt \
  --source /data/SITRA.TR.7173.txt
```

The importer normalizes dates and coordinates, stores source rows in Neo4j, and reports loaded and skipped records. Application startup never imports data.
