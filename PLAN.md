# Vietnam Conflict Data Explorer MVP Plan

## Goal

Build a polished, container-ready web app for exploring NARA's *Situation Report Army* records (catalog ID 604416). Users can search and filter by date, inspect results on a map and creation-date timeline, and view the connections for an individual record. Keep the feature set limited to these workflows.

## Repository

GitHub repository: https://github.com/otto95/sitra-viewer

## Phase 1: Project foundation

- [x] Confirm NARA's source-level metadata and advertised file formats needed to assess search, dates, locations, and record relationships. Record confirmed details and defer exact source-file layouts to Phase 3.
- [x] Use Neo4j Community Edition as the only application database, running locally at no cost; no relational database or hosted database service.
- [x] Scaffold a Python API backend and a client-rendered React app in `frontend/` using current, widely adopted libraries.
- [x] Add `.gitignore`, dependency manifests/lockfiles, local configuration examples, and container build/run configuration for the app and local Neo4j Community Edition, with a persistent local data volume.
- [x] Scaffold a separate, documented import command entry point; starting the app must not trigger data ingestion. Implement the loader in Phase 3.
- [x] Add a minimal README with setup, run, and separate import instructions.
- [x] Establish a repeatable local development workflow and a health check for the backend.

**Success criteria**

- [x] A clean checkout can install dependencies and start the frontend, backend, and local Neo4j Community Edition using documented commands or containers; app startup does not import data, and import has a separate documented command.
- [x] The frontend can reach the backend health endpoint; no user credentials or user management are required.

## Phase 2: Graph schema from ontology

- [ ] Inspect `docs/ontology_diagram.drawio` and identify its entity types, properties, and relationship types.
- [ ] Translate the ontology into a Neo4j graph model and Cypher setup, including only the constraints and indexes needed for record identity, search, date filtering, and relationship traversal.
- [ ] Define how NARA fields map to ontology properties and relationships; identify metadata that can support inferred links between records, including shared unit, place, and date. Preserve source UTM/MGRS values alongside normalized coordinates.
- [ ] Compare relationships apparent in the source data with those expressible in the ontology. Recommend and document schema modifications wherever a useful relationship cannot be represented; incorporate needed changes before finalizing the schema.
- [ ] Store metadata-inferred associations as possible links, distinct from source-stated relationships, and record the shared metadata supporting each inference. Support promoting a possible link to a definite link while retaining its origin/evidence.
- [ ] Validate that representative NARA records and their associations can be represented by the schema before implementing the one-time import.

**Success criteria**

- [ ] The graph schema is traceable to `docs/ontology_diagram.drawio`, with any interpretation decisions documented.
- [ ] Any schema changes recommended after reviewing the data are documented with their rationale and reflected in the finalized model.
- [ ] A representative sample can be modeled and queried in Neo4j, including source-stated relationships and metadata-inferred possible links; a possible link can be promoted to a definite link without losing its evidence or provenance.
- [ ] The schema supports the required search and date-filter workflows without adding unrelated data concepts.
- [ ] The schema is documented under the docs folder

## Phase 3: One-time data ingestion and API

- [ ] Provide a separate import command that loads the selected NARA source into the locally running Neo4j Community Edition database, preserving source identifiers and useful metadata. Keep the imported graph data local; routine refreshes are out of scope. App startup must not run this command automatically.
- [ ] Select the NARA source that provides the most usable records for the MVP; normalize all imported text fields for free-text search and relationship references while retaining source provenance. Normalize every date to ISO 8601 calendar-date format (`YYYY-MM-DD`). Treat a date value with exactly five digits or a trailing `J` as a Julian date; interpret all dates as falling between 1965 and 1973, convert Julian dates to their corresponding Gregorian calendar dates, and retain the original date value for provenance.
- [ ] Convert legacy UTM values to latitude/longitude using the supplied `convert_to_latlong` approach. The source UTM values omit the grid zone designator (GZD); try each of Vietnam's four GZDs (`48Q`, `49Q`, `48P`, and `49P`) with the UTM value, select the GZD that yields a valid MGRS value, then convert that MGRS value to latitude/longitude. Store the original UTM value, selected GZD/MGRS value, and resulting coordinates in Neo4j for map use; leave coordinates empty when the value is missing or no valid MGRS value can be produced.
- [ ] Create inferred record links from shared metadata such as unit, place, or date, using the finalized graph schema and preserving the evidence for each inferred link.
- [ ] Define a small API for free-text search across all imported text fields, pagination, date-range filtering, record details, map-ready results, and a selected record's related records. Include an operation to promote a possible link to a definite link.
- [ ] Handle incomplete or unparseable source fields consistently so records without valid dates, coordinates, or known links remain usable where applicable; do not invent a normalized date when the source value cannot be interpreted under the date rules.

**Success criteria**

- [ ] The initial import reports how many records were loaded or skipped and completes against a clean database without manual edits.
- [ ] API responses have documented, stable shapes and return enough information for all required views.
- [ ] Unit tests cover import normalization, including ISO date output, five-digit and `J`-suffixed Julian dates across the 1965–1973 year range, calendar-date inputs, and missing or unparseable dates; also cover search/date filtering, pagination, detail retrieval, relationship lookup, and promotion of possible links to definite links.
- [ ] Search tests verify matches across every imported text field, not only titles or descriptions.
- [ ] Unit tests cover known conversions for all four GZDs, selection of the GZD that produces a valid MGRS value, missing values, and values for which no valid MGRS value can be produced; verify converted coordinates are used in map results.

## Phase 4: Explorer experience

- [ ] Build a cohesive responsive interface in `frontend/` with a clear search field, date limits, result count, and readable record list.
- [ ] Apply the supplied palette: Olive Drab `#556B2F`, Field Green `#3F5940`, Coyote Tan `#B58B5A`, Deep Charcoal `#242820`, Warm Gray `#77766D`, and Parchment `#F3F0E6`.
- [ ] Plot the current search results on an interactive map and make map selection open the corresponding record.
- [ ] Plot results along a timeline by creation date, keeping date filtering consistent with search results.
- [ ] Provide a record detail view with a network graph of that record and its associated records. Show metadata-inferred associations as possible links, visibly labeled as such, and provide a user action to change a possible link to a definite link; reflect the updated status in the graph.
- [ ] Include clear loading, empty, and error states; keep controls and navigation limited to the MVP workflows.

**Success criteria**

- [ ] Search terms and date limits update the same result set shown in the list, map, and timeline.
- [ ] Selecting a result from the list or map opens its details and relationship graph; possible links are labeled, and promoting one changes its displayed status to definite.
- [ ] The layout remains usable at desktop and narrow/mobile widths, with legible labels, keyboard-accessible controls, and no horizontal overflow.

## Phase 5: Verification and polish

- [ ] Run backend and frontend unit tests; add focused tests for important UI behavior and data transformations.
- [ ] Add Playwright end-to-end coverage for search, date filtering, map/timeline synchronization, record relationship navigation, and promoting a possible link to a definite link.
- [ ] Exercise the containerized app with representative imported data and fix defects found in integration testing.
- [ ] Review accessibility basics, responsive layout, visual consistency, and performance for the intended dataset size.
- [ ] Confirm documentation accurately describes import, configuration, tests, and startup.

**Success criteria**

- [ ] Unit and end-to-end suites pass from documented commands.
- [ ] A fresh container startup can serve the app against the database; after the documented separate import command loads the dataset, the core workflows work without manual database edits.
- [ ] Final review confirms all MVP requirements work and no unrelated features have been added.

## Phase 6: Ready for use

- [ ] Start the completed app in the workspace using the documented container workflow.
- [ ] Verify the running frontend and API are reachable and the core search workflow works against the available dataset.
- [ ] Record the local URL, startup command, and any data-source limitation in the final handoff.

**Success criteria**

- [ ] The app is running and ready for the user to explore, with a clear note if NARA access or source data availability limits the loaded records.
