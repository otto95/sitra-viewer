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

- [x] Inspect `docs/ontology_diagram.drawio` and identify its entity types, properties, and relationship types.
- [x] Translate the ontology into a Neo4j graph model and Cypher setup, including only the constraints and indexes needed for record identity, search, date filtering, and relationship traversal.
- [x] Define how NARA fields map to ontology properties and relationships; identify metadata that can support inferred links between records, including shared unit, place, and date. Preserve source UTM/MGRS values alongside normalized coordinates.
- [x] Compare relationships apparent in the source data with those expressible in the ontology. Recommend and document schema modifications wherever a useful relationship cannot be represented; incorporate needed changes before finalizing the schema.
- [x] Store metadata-inferred associations as possible links, distinct from source-stated relationships, and record the shared metadata supporting each inference. Support promoting a possible link to a definite link while retaining its origin/evidence.
- [x] Validate representative NARA record fields and associations against the schema before implementing the one-time import. The official 1966–1968 fixed-width layout and a representative record row were inspected; the database sample validates source groups, periodic sets, possible-link evidence, promotion, search, and date filtering. Bulk parsing remains Phase 3.

**Success criteria**

- [x] The graph schema is traceable to `docs/ontology_diagram.drawio`, with any interpretation decisions documented.
- [x] Any schema changes recommended after reviewing the data are documented with their rationale and reflected in the finalized model.
- [x] A representative sample can be modeled and queried in Neo4j, including source-stated relationships and metadata-inferred possible links; a possible link can be promoted to a definite link without losing its evidence or provenance.
- [x] The schema supports the required search and date-filter workflows without adding unrelated data concepts.
- [x] The schema is documented under the docs folder.

## Phase 3: One-time data ingestion and API

- [x] Provide a separate import command that loads the selected NARA source into the locally running Neo4j Community Edition database, preserving source identifiers and useful metadata. Keep the imported graph data local; routine refreshes are out of scope. App startup must not run this command automatically.
- [x] Select the four ASCII translations covering the full 1966–1973 period; normalize all imported text fields for free-text search and relationship references while retaining source provenance. Normalize every parseable date to ISO 8601 calendar-date form (`YYYY-MM-DD`). Treat a date value with exactly five digits or a trailing `J` as a Julian date; interpret years as 1965–1973, convert valid Julian dates to Gregorian dates, and retain original date values.
- [ ] Decode coded source values to readable labels using the authoritative code descriptions and value tables in NARA's [SITRA technical documentation](https://catalog.archives.gov/medialz/electronic-records/rg-218/SITRA/131.1DP.pdf). Cover every coded field with a documented mapping, including data type, force/service nationality, country, operation/action type, province, objective and objective description, unit size, and loss/incident codes. Preserve the original code alongside the readable value; leave unknown or undocumented codes visible as raw codes rather than guessing.
- [x] Convert legacy UTM values to latitude/longitude with `convert_to_latlong`. The source values omit the grid zone designator (GZD); try each of Vietnam's four GZDs (`48Q`, `49Q`, `48P`, and `49P`), accept a unique MGRS interpretation inside that GZD's Vietnam bounds, then retain the selected GZD/MGRS and converted coordinates. Missing or unconvertible coordinates remain absent.
- [x] Create metadata-inferred links from shared unit and exact MGRS location, and add shared date as evidence when present. Source-stated control groups remain distinct; evidence and origin are retained for promotion.
- [x] Define API endpoints for free-text search across all imported text fields, pagination, date-range filtering, record details, map-ready results, related records, and possible-link promotion. Document stable routes and response shapes.
- [x] Keep records with incomplete or unparseable source values usable; preserve unparseable raw dates and UTM values without inventing normalized values.

**Success criteria**

- [x] The initial import reports loaded/skipped counts and completed against a clean database without manual edits: 742,591 loaded and 0 skipped.
- [x] API responses have documented, stable shapes and return enough information for all required views.
- [x] Unit and Neo4j integration tests cover import/date normalization, Julian and calendar dates, missing and invalid values, search/date filtering, pagination, details, relationship lookup, and possible-link promotion.
- [x] Search coverage checks every source field is included in indexed report text.
- [ ] Tests verify documented code-to-label mappings across fixed and periodic fields, readable values are exposed to search/detail consumers, original codes are retained, and unknown codes do not get an invented label.
- [x] Tests cover known conversions for all four GZDs, selection of the matching GZD, missing or invalid values, and coordinates in map-ready search results.

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
