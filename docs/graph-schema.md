# SITRA graph schema

The [ontology](ontology_description.md) contains the source field mappings. `backend/cypher/schema.cypher` defines the Neo4j constraints and indexes. Schema setup is idempotent and non-destructive: it does not migrate, delete, or read legacy `Report` or `SourceGroup` data. Use a fresh database for the canonical import; do not delete an existing volume. Existing confirmations are not migrated.

## Source and entity model

| Node | Storage and traversal |
| --- | --- |
| `DataRecord` | One logical report per exact 12-character control key `dataRecordId`, including blanks. Continuation rows belong to that node. Raw control and fixed fields live here alongside the normalized Neo4j `reportDate` and `searchText`. Flag conflicting fixed fields during import; never silently overwrite them. |
| `PeriodicSet` | One `HAS_PERIODIC_SET` child per populated set occurrence. Keep the set number, original line field, raw property values, source file, and row or offset. Construct `periodicSetId` from the source file identity, row or offset, and set number, not from a potentially repeated line identifier. |
| `Event`, `Unit`, `Location` | Preserve the subtype and provenance on `REPORTS`, `REFERENCES_UNIT`, `PARTICIPATED_IN`, `REPORTED_UNDER`, `REPORTS_GEOGRAPHY`, `HAS_OBJECTIVE_LOCATION`, and `IN_COUNTRY` as applicable. A repeated set 2 coordinate can describe the same Operation; summary counts do not create Events. |
| `Material` | Shared catalog entry labeled `Weapon`, `Ammunition`, or `Provision`, with `materialKey`, `kind`, and `name`. Set 4 occurrences link to it with `ABOUT`; quantities and provenance stay on the occurrence. Unknown codes stay queryable without an `ABOUT` edge. |

There is no definite record-to-record association based on the control key. A shared key identifies one node. Validate source-stated links to events, units, and locations instead.

## Inferred links

After loading the source-backed graph, `infer_record_links` finds distinct records with two valid report dates at most seven calendar days apart (inclusive) and at least one shared resolved Unit (`resolved: true`) or specific Location (`specific: true`, never Country). Use `specific` for concrete matches such as a named province or a verified shared objective location, not an ambiguous grid reference. The writer must link a verified shared objective to each record with `REPORTS_GEOGRAPHY` before it can support inference. A shared date, country, unresolved unit, or material type alone does not qualify.

`RELATED_TO` edges use a canonical direction and pair ID, with `status=possible`, `origin=metadata_inferred`, `evidence`, and `daysApart`. Promotion sets `status=definite` and adds confirmation metadata while retaining the evidence and inferred origin. APIs and UIs should render these links as **user-confirmed**, not source-stated. Re-running inference does not overwrite a confirmed edge's evidence.

## MVP query contracts

- **Search and timeline:** `data_record_search` indexes normalized imported text on `DataRecord.searchText`; `data_record_date` indexes the normalized report date. Results, date counts and timeline entries are per Data Record, not per periodic occurrence.
- **Map:** `record_map_points` returns all set 2 occurrences with verified coordinates, including raw UTM, selected GZD, constructed MGRS, and a stable point ID. Each marker opens its owning Data Record. Unresolved or ambiguous references remain in record details and produce no markers. Phase 3 must verify the grid zone rather than select the first syntactically valid candidate.
- **Material network:** `record_material_network` traverses set 4 observations to typed materials and back to other records. In the MVP UI these are visible, selectable material nodes; the traversal does not create direct inferred record links.

## Run and validate

With the Compose stack running, run:

```sh
docker compose exec backend uv run --no-sync python -m app.graph_schema setup
docker compose exec backend uv run --no-sync python -m app.graph_schema validate-sample
```

The validation uses a synthetic graph based on the documented record layout. It verifies repeated occurrence identity, source-backed traversal, material navigation, multiple map points with an ambiguous reference excluded, seven-day eligibility, confirmation provenance, and search/date filtering. It removes the tagged sample nodes afterward. Bulk parsing, coordinate verification and API/UI wiring are subsequent phases.
