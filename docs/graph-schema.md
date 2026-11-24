# Graph schema

The graph follows `ontology_diagram.drawio` and the NARA source notes in [nara-source.md](nara-source.md). The official SITRA translation layout `SITRA.TR.LAY.txt` (downloadable from NARA file unit 1402152) was inspected alongside the first fixed-width data rows. It defines a 298-column record with five control fields at columns 1–12 (`DATE`, `DATAT`, `SERAL`, `CORP`, `PART`), a fixed set at columns 13–78, and seven periodic sets. Schema setup is idempotent and is defined in `backend/cypher/schema.cypher`.

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
| `DATAT`, `SERAL`, `CORP`, `PART` (columns 7–12) | `Report.reportType`, `paragraphNumber`, `militaryRegion`, `part` | The source layout labels `SERAL` as Paragraph Number and `CORP` as Military Region. Preserve raw control values. |
| Serial / control number | `Report.serial`, `sourceControlNumber` | Preserve original values as supplied. |
| `UDATE` (Date of Last Update, fixed columns 43–47) | `FixedSet.updateDate` | Five-character source date; retain raw value and normalize to ISO date in Phase 3. |
| Initiation Date and Termination Date | `Report.initiationDate`, `Report.terminationDate` | Optional; retain only when parseable. Operation-specific times map to `startDateTime` and `endDateTime` when provided. |
| Operation type and name/code | `HAS_OPERATION_TYPE`; report properties `operationName`, `operationCode` | Operation types use the shared code-list node. |
| Primary and additional province | `HAS_PRIMARY_PROVINCE`, `HAS_SECONDARY_PROVINCE` | Code-list references support shared-place traversal. |
| `UTM` (Second Set, columns 111–118) | `Report.sourceUtm` | Preserve the original value without mutation. |
| Selected GZD and constructed MGRS | `Report.mgrsGzd`, `Report.sourceMgrs` | Preserve the chosen grid designator and resulting MGRS value alongside the raw UTM value. |
| Converted point | `Report.latitude`, `Report.longitude` | Numeric coordinates used by the map. Leave absent if conversion fails. |
| Imported text | `Report.searchText` | Normalized concatenation of all imported text fields, indexed for free-text search. |

The source layout confirms the field positions and periodic set types; Phase 3 will finalize exact source-record identity and periodic-row keys while implementing the loader. A representative source control row begins `660520W003` (Message Date 1966-05-20, Data Type `W`, Paragraph Number `003`); other control values may be blank. Date parsing follows the Julian-date rule already recorded in `PLAN.md`; parsed values are stored as Neo4j temporal `DATE` properties and serialized as ISO calendar dates.

## Record associations

NARA describes related multi-record operations and summaries as repeating the five control values from columns 1–12: Message Date (`DATE`), Data Type (`DATAT`), Paragraph Number (`SERAL`), Military Region (`CORP`), and Part (`PART`). Each complete control tuple maps to a `(:SourceGroup {groupKey})`; related reports connect to it through `MEMBER_OF`. The graph view can traverse the group to show these source-stated associations as definite. This avoids creating every pair in a group as a separate relationship.

Associations inferred from shared unit, province/place, or report date use one canonical direction for `(:Report)-[:RELATED_TO]->(:Report)` and these properties:

- `linkId`: SHA-256 of the UTF-8 report IDs in byte-sorted order with four-byte length prefixes, making the pair identity order-independent.
- `status`: `possible` or `definite`.
- `origin`: `metadata_inferred`.
- `evidence`: strings naming each shared value, such as `shared_unit:<unitKey>` or `shared_date:YYYY-MM-DD`.
- `confirmedAt` and `confirmedBy`: set when a user promotes a possible link.

Promotion changes `status` to `definite` and adds confirmation fields; it leaves `origin` and `evidence` intact. The promotion helper in `backend/app/graph_schema.py` only updates a still-possible inferred link.

The repeated source group is only created when all five control values are present. A missing control value is not treated as a wildcard. The exact source group key serialization and unit identity key will be finalized while implementing the Phase 3 loader.

## Constraints and indexes

`schema.cypher` adds uniqueness constraints for report, fixed-set, periodic-set, unit, source-group, and code-list identities, plus `RELATED_TO.linkId` so repeated graph writes can use `MERGE`. It adds a range index on `Report.reportDate` for date filters and a full-text index on `Report.searchText` for the search box. Relationship traversal uses Neo4j's adjacency and needs no separate traversal index. Map coordinates are returned with date-filtered reports, so no spatial index is added for this MVP.

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

## Run and validate

With the Compose stack running:

```sh
docker compose exec backend uv run --no-sync python -m app.graph_schema setup
docker compose exec backend uv run --no-sync python -m app.graph_schema validate-sample
```

The sample validation creates three clearly namespaced demo reports, proves the source-group, periodic-unit, and date-filter traversals, promotes one possible association, checks that its origin and evidence remain unchanged, and removes its sample nodes. It does not load or alter NARA records.
