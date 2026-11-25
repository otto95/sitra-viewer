# API

The FastAPI service reads the local Neo4j database. Application startup does not ingest or modify records. Dates in API responses use ISO `YYYY-MM-DD`.

## Search

`GET /api/records`

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `q` | string | omitted | Full-text search across source fields. |
| `from` | date | omitted | Inclusive lower bound on Message Date. |
| `to` | date | omitted | Inclusive upper bound on Message Date. |
| `offset` | integer | `0` | Number of matching rows to skip. |
| `limit` | integer | `50` | Page size, from 1 to 200. |

Example response:

```json
{
  "items": [
    {
      "record": {
        "recordId": "SITRA.TR.6668.txt:17",
        "reportDate": "1966-05-20",
        "reportDateRaw": "660520",
        "reportType": "W",
        "sourceUtm": "WH000114",
        "mgrsGzd": "48Q",
        "sourceMgrs": "48QWH000114",
        "latitude": 19.9997,
        "longitude": 105.0005,
        "searchText": "..."
      },
      "score": 0.89
    }
  ],
  "total": 1,
  "offset": 0,
  "limit": 50
}
```

Records with a missing or unparseable date remain searchable without date bounds. Their `reportDate` is absent, and they do not match a date-filtered query. Records with unconvertible coordinates retain `sourceUtm` and omit `mgrsGzd`, `sourceMgrs`, `latitude`, and `longitude`.

## Record details and associations

- `GET /api/records/{recordId}` returns `{ "record": ..., "fixedSets": [...], "periodicSets": [...] }`.
- `GET /api/records/{recordId}/related` returns `{ "recordId": ..., "items": [...] }`. Each item contains its `record`, `status`, `origin`, and `evidence`. `origin` is `source_control_group`, `metadata_inferred`, or `source_control_group+metadata_inferred` when both apply. Source-control groups appear as definite associations; inferred links appear as possible until promoted.
- `POST /api/links/{linkId}/promote` changes a possible metadata-inferred link to definite and returns `{ "linkId": ..., "status": "definite" }`. A missing or already definite link returns HTTP 409. Origin and evidence remain unchanged.

An unknown record returns HTTP 404. Search limits outside the supported range, invalid dates, or reversed date bounds return HTTP 422.
