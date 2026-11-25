# Graph schema

The graph follows `ontology_diagram.drawio` and the NARA source notes in [nara-source.md](nara-source.md). The official SITRA translation layout `SITRA.TR.LAY.txt` and technical documentation (downloadable from NARA file unit 1402152) were inspected alongside the first fixed-width data rows. Each translated row is 298 columns with five control fields at columns 1–12 (`DATE`, `DATAT`, `SERAL`, `CORP`, `PART`), a fixed set at columns 13–78, and seven periodic sets. Schema setup is idempotent and is defined in `backend/cypher/schema.cypher`.

## Model

| Ontology concept | Neo4j representation | Mapping notes |
| --- | --- | --- |
| Report | `(:Report)` | One source record, keyed by `recordId`. Report subtypes (`LargeScaleOperation`, `SmallScaleOperation`, `EnemyInitiated`, `WeeklySummary`) are additional labels on the same node. |
| FixedSet | `(:FixedSet)` | One node per report, connected by `HAS_FIXED_SET`. |
| PeriodicSet | `(:PeriodicSet)` | One node per repeated source row, connected from `FixedSet` by `HAS_PERIODIC_SET`. `kind` identifies the ontology content type; the type-specific fields remain on the periodic-set node. |
| Unit | `(:Unit)` | A normalized unit identity keyed by `unitKey`; a unit periodic set refers to it with `HAS_UNIT`, allowing reports to share a unit node. |
| Nationality, Country, OperationType, Province | Same-named nodes | Code-list values keyed by `code`; records connect through `HAS_NATIONALITY`, `HAS_COUNTRY`, `HAS_OPERATION_TYPE`, `HAS_PRIMARY_PROVINCE`, and `HAS_SECONDARY_PROVINCE`. |
| AircraftService | `(:AircraftService)` | Represents an aircraft service/type and is connected from the relevant periodic set with `HAS_AIRCRAFT_SERVICE`. |
| Loss, Action, Incidents, RVNStats, LossStats, CombinedOperation | PeriodicSet `kind` values | Their source properties map to the corresponding periodic-set node. This keeps each repeated source row as one node while retaining its ontology type. |

The ontology's `hasFixedSet` maps to `HAS_FIXED_SET`; `hasOperationType`, `hasNationality`, `hasCountry`, and primary/secondary province references map to the lookup relationships in the table. `hasLoss`, `describedBy`, `hasIncidents`, and `hasStats` describe typed repeated rows and are represented by `HAS_PERIODIC_SET` plus the row's `kind`. `hasParticipant` is represented by a unit periodic set and `HAS_UNIT`. `hasAircraftService` maps to `HAS_AIRCRAFT_SERVICE` when those source endpoints are present. The ontology's `isPartOf / includes` relation maps conceptually to `PART_OF`; exact source endpoints must be checked against the downloadable file layout before importing it. The diagram's `hasConat` typo is not expanded because its intended meaning is unclear.

The diagram has a few incomplete or ambiguous edges. `hasConat` is not expanded because its intended meaning is unclear, and unlabeled lines are not assigned semantics. The `hasFixedSet` edge is drawn from the `report_type` property cell; it is interpreted as a relationship from the Report entity to FixedSet. Duplicate Nationality boxes in the diagram refer to one code-list entity.

## NARA field mapping

| NARA field or concept | Neo4j property/relationship | Notes |
| --- | --- | --- |
| Stable source record identifier | `Report.recordId` | The source layout must be inspected before choosing its exact construction; `cntrl` alone is not assumed unique. |
| `DATE` (Message Date, columns 1–6) | `Report.reportDate` | The record creation/timeline date. Stored as Neo4j `DATE`; API output is ISO `YYYY-MM-DD`. |
| `DATAT`, `SERAL`, `CORP`, `PART` (columns 7–12) | `Report.reportType`, `paragraphNumber`, `militaryRegion`, `part` | `DATAT` codes `S`, `L`, `E`, and `W` add the ontology labels SmallScaleOperation, LargeScaleOperation, EnemyInitiated, and WeeklySummary. `SERAL` is Paragraph Number and `CORP` is Military Region. |
| `SERAL` paragraph/control number | `Report.serial`, `paragraphNumber` | Preserve the source value as supplied. |
| `UDATE` (Date of Last Update, fixed columns 43–47) | `FixedSet.updateDate` | Five-character Julian source date; preserve its original text in `updateDateRaw` and normalize valid values. |
| `DTEI`, `DTET`, `HOURT`, `HOURI` | `Report.initiationDate`, `terminationDate`, `initiationHour`, `terminationHour` | Dates are optional and normalized independently; hours remain the original four-character source values. |
| Operation type and name/code | `HAS_OPERATION_TYPE`; report properties `operationName`, `operationCode` | Operation types use the shared code-list node. |
| Primary and additional province | `HAS_PRIMARY_PROVINCE`, `HAS_SECONDARY_PROVINCE` | Code-list references support shared-place traversal. |
| `UTM` (Second Set, columns 111–118) | `Report.sourceUtm` | The source documentation describes this as a two-letter 100 km grid square plus six digits. Preserve the original value without mutation. |
| Selected GZD and constructed MGRS | `Report.mgrsGzd`, `Report.sourceMgrs` | Preserve the chosen grid designator and resulting MGRS value alongside the raw UTM value. |
| Converted point | `Report.latitude`, `Report.longitude` | Numeric coordinates used by the map. Leave absent if conversion fails. |
| Imported text | `Report.searchText` | Normalized concatenation of all imported text fields, indexed for free-text search. |

The source layout confirms field positions and periodic set types. Source record identity is the translated file name plus one-based row number; that keeps every physical source record distinct even where a control tuple repeats. Periodic-row identity adds its set number. A representative source row begins `660520W003` (Message Date 1966-05-20, Data Type `W`, Paragraph Number `003`); other control values may be blank. Message, initiation, and termination dates use `YYMMDD`; update dates use `YYDDD`. Five-digit values and values ending in `J` are normalized as Julian dates under the rule in `PLAN.md`; parsed values are stored as Neo4j temporal `DATE` properties and serialized as ISO calendar dates. Original values remain on `reportDateRaw`, `updateDateRaw`, `initiationDateRaw`, and `terminationDateRaw`.

## Record associations

NARA describes related multi-record operations and summaries as repeating the five control values from columns 1–12: Message Date (`DATE`), Data Type (`DATAT`), Paragraph Number (`SERAL`), Military Region (`CORP`), and Part (`PART`). Each complete control tuple maps to a `(:SourceGroup {groupKey})`; related reports connect to it through `MEMBER_OF`. The graph view can traverse the group to show these source-stated associations as definite. This avoids creating every pair in a group as a separate relationship.

Associations inferred from a shared unit or exact converted MGRS grid square use one canonical direction for `(:Report)-[:RELATED_TO]->(:Report)`. For each shared unit or location group, the lexicographically earliest record is the anchor and is linked to each other group member. This sparse network represents shared metadata without creating every possible pair in large groups. A shared report date is retained as additional evidence when the candidate pair already shares a unit or exact location. Date alone does not create pairs because it would connect broad daily cohorts with weak evidence. Inferred edges use these properties:

- `linkId`: `related:<first-record-id>|<second-record-id>`, with UTF-8 byte-sorted IDs, making pair identity order-independent. Imported IDs use escaped source file names and row numbers, so the separator is unambiguous.
- `status`: `possible` or `definite`.
- `origin`: `metadata_inferred`.
- `evidence`: strings naming each shared value, such as `shared_unit:<unitKey>` or `shared_date:YYYY-MM-DD`.
- `confirmedAt` and `confirmedBy`: set when a user promotes a possible link.

Promotion changes `status` to `definite` and adds confirmation fields; it leaves `origin` and `evidence` intact. The promotion helper in `backend/app/graph_schema.py` only updates a still-possible inferred link.

The repeated source group is only created when all five control values are present. A missing control value is not treated as a wildcard. The group key hashes the normalized JSON control tuple; a unit key hashes service nationality, company, battalion, brigade, and division identity values.

## Constraints and indexes

`schema.cypher` adds uniqueness constraints for report, fixed-set, periodic-set, unit, aircraft-service, source-group, and code-list identities, plus `RELATED_TO.linkId` so repeated graph writes can use `MERGE`. It adds range indexes on `Report.reportDate` and `Report.sourceMgrs` for date filters and exact-location inference, plus a full-text index on `Report.searchText` for the search box. Relationship traversal uses Neo4j's adjacency and needs no separate traversal index. Map coordinates are returned with date-filtered reports, so no spatial index is added for this MVP.

## Useful queries

Search text and apply the creation-date interval:

```cypher
MATCH (report:Report)
SEARCH report IN (
    FULLTEXT INDEX report_search
    FOR $query
    LIMIT 3000000
)
SCORE AS score
WHERE ($fromDate IS NULL OR report.reportDate >= date($fromDate))
  AND ($toDate IS NULL OR report.reportDate <= date($toDate))
RETURN report, score
ORDER BY score DESC, report.reportDate, report.recordId
SKIP $offset
LIMIT $limit
```

The search-index candidate limit is above the 2.28 million logical records NARA reports for this series, so date filtering and pagination happen after all matching candidates for the one-time local snapshot are considered. Revisit this cap if the selected source or dataset changes.

Traverse a selected report's direct inferred links:

```cypher
MATCH (selected:Report {recordId: $recordId})-[link:RELATED_TO]-(related:Report)
RETURN related, link.status AS status, link.origin AS origin, link.evidence AS evidence
```

Traverse source-stated report groups:

```cypher
MATCH (selected:Report {recordId: $recordId})-[:MEMBER_OF]->(group:SourceGroup)
      <-[:MEMBER_OF]-(related:Report)
RETURN related, 'definite' AS status, 'source_control_group' AS origin, group
```

## API

Stable response shapes and routes are described in [api.md](api.md). The API starts independently of the importer; it reads the local Neo4j snapshot and exposes search, details, related records, and link promotion.

## Run and validate

With the Compose stack running:

```sh
docker compose exec backend uv run --no-sync python -m app.graph_schema setup
docker compose exec backend uv run --no-sync python -m app.graph_schema validate-sample
docker compose run --rm backend uv run --no-sync python -m app.import_data --source /data/SITRA.TR.6668.txt --source /data/SITRA.TR.69.txt --source /data/SITRA.TR.70.txt --source /data/SITRA.TR.7173.txt
```

The importer is separate from app startup and accepts one or more local ASCII translations. It reports loaded rows, malformed rows skipped, records without a parseable date, and records without coordinates. Re-running it uses stable record and relationship identities. The sample validation creates three clearly namespaced demo reports, proves the source-group, periodic-unit, and date-filter traversals, promotes one possible association, checks that its origin and evidence remain unchanged, and removes its sample nodes.
