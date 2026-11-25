import os
from datetime import date
from functools import lru_cache
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query
from neo4j import Driver, GraphDatabase

from app.graph_schema import promote_possible_link

app = FastAPI(title="SITRA Viewer API", version="0.2.0")
SEARCH_CANDIDATE_LIMIT = 3_000_000


@lru_cache
def get_driver() -> Driver:
    return GraphDatabase.driver(os.getenv("NEO4J_URI", "bolt://localhost:7687"))


def _database() -> str:
    return os.getenv("NEO4J_DATABASE", "neo4j")


def _serialize(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    if hasattr(value, "to_native"):
        value = value.to_native()
    if isinstance(value, date):
        return value.isoformat()
    return value


def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/health", tags=["health"])
def health_endpoint() -> dict[str, str]:
    return health()


def _date_filter(from_date: date | None, to_date: date | None) -> tuple[str, dict[str, Any]]:
    conditions = []
    parameters: dict[str, Any] = {}
    if from_date is not None:
        conditions.append("report.reportDate >= $from_date")
        parameters["from_date"] = from_date
    if to_date is not None:
        conditions.append("report.reportDate <= $to_date")
        parameters["to_date"] = to_date
    return (" AND ".join(conditions) if conditions else "true"), parameters


def search_records(
    driver: Driver,
    q: str | None,
    from_date: date | None,
    to_date: date | None,
    offset: int,
    limit: int,
) -> dict[str, Any]:
    date_clause, date_parameters = _date_filter(from_date, to_date)
    if q and q.strip():
        prefix = f"""
            MATCH (report:Report)
            SEARCH report IN (
                FULLTEXT INDEX report_search
                FOR $query
                LIMIT {SEARCH_CANDIDATE_LIMIT}
            )
            SCORE AS score
            WHERE {date_clause}
        """
        parameters = {**date_parameters, "query": q.strip(), "offset": offset, "limit": limit}
        total_query = prefix + " RETURN count(report) AS total"
        results_query = prefix + """
            RETURN report, score
            ORDER BY score DESC, report.reportDate, report.recordId
            SKIP $offset LIMIT $limit
        """
    else:
        prefix = f"MATCH (report:Report) WHERE {date_clause}"
        parameters = {**date_parameters, "offset": offset, "limit": limit}
        total_query = prefix + " RETURN count(report) AS total"
        results_query = prefix + """
            RETURN report, 0.0 AS score
            ORDER BY report.reportDate, report.recordId
            SKIP $offset LIMIT $limit
        """

    with driver.session(database=_database()) as session:
        total_record = session.run(total_query, parameters).single()
        records = session.run(results_query, parameters).data()
    return {
        "items": [
            {"record": _serialize(dict(row["report"])), "score": row["score"]}
            for row in records
        ],
        "total": total_record["total"] if total_record else 0,
        "offset": offset,
        "limit": limit,
    }


@app.get("/api/records", tags=["records"])
def get_records(
    q: str | None = None,
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    driver: Driver = Depends(get_driver),
) -> dict[str, Any]:
    if from_date is not None and to_date is not None and from_date > to_date:
        raise HTTPException(status_code=422, detail="from must be on or before to")
    return search_records(driver, q, from_date, to_date, offset, limit)


@app.get("/api/records/{record_id}", tags=["records"])
def get_record(record_id: str, driver: Driver = Depends(get_driver)) -> dict[str, Any]:
    with driver.session(database=_database()) as session:
        result = session.run(
            """
            MATCH (report:Report {recordId: $record_id})
            OPTIONAL MATCH (report)-[:HAS_FIXED_SET]->(fixed:FixedSet)
            OPTIONAL MATCH (fixed)-[:HAS_PERIODIC_SET]->(periodic:PeriodicSet)
            RETURN report,
                   collect(DISTINCT CASE WHEN fixed IS NULL THEN null ELSE properties(fixed) END) AS fixedSets,
                   collect(DISTINCT CASE WHEN periodic IS NULL THEN null ELSE properties(periodic) END) AS periodicSets
            """,
            record_id=record_id,
        ).single()
    if result is None:
        raise HTTPException(status_code=404, detail="record not found")
    return {
        "record": _serialize(dict(result["report"])),
        "fixedSets": _serialize(result["fixedSets"]),
        "periodicSets": _serialize(result["periodicSets"]),
    }


@app.get("/api/records/{record_id}/related", tags=["records"])
def get_related_records(record_id: str, driver: Driver = Depends(get_driver)) -> dict[str, Any]:
    with driver.session(database=_database()) as session:
        exists = session.run(
            "MATCH (report:Report {recordId: $record_id}) RETURN report.recordId AS id",
            record_id=record_id,
        ).single()
        if exists is None:
            raise HTTPException(status_code=404, detail="record not found")
        source_links = session.run(
            """
            MATCH (report:Report {recordId: $record_id})-[:MEMBER_OF]->(group:SourceGroup)
                  <-[:MEMBER_OF]-(related:Report)
            WHERE related.recordId <> report.recordId
            RETURN related, group,
                   ['source_group:' + group.groupKey] AS evidence
            """,
            record_id=record_id,
        ).data()
        inferred_links = session.run(
            """
            MATCH (report:Report {recordId: $record_id})
                  -[link:RELATED_TO]-(related:Report)
            RETURN related, link.status AS status, link.origin AS origin,
                   link.evidence AS evidence
            """,
            record_id=record_id,
        ).data()

    related: dict[str, dict[str, Any]] = {}
    for row in source_links:
        node = _serialize(dict(row["related"]))
        related[node["recordId"]] = {
            "record": node,
            "status": "definite",
            "origin": "source_control_group",
            "evidence": row["evidence"],
        }
    for row in inferred_links:
        node = _serialize(dict(row["related"]))
        record_id_value = node["recordId"]
        if record_id_value in related:
            related[record_id_value]["evidence"] = sorted(
                set(related[record_id_value]["evidence"] + row["evidence"])
            )
            related[record_id_value]["origin"] = "source_control_group+metadata_inferred"
            continue
        related[record_id_value] = {
            "record": node,
            "status": row["status"],
            "origin": row["origin"],
            "evidence": row["evidence"],
        }
    return {"recordId": record_id, "items": list(related.values())}


@app.post("/api/links/{link_id}/promote", tags=["links"])
def promote_link(link_id: str, driver: Driver = Depends(get_driver)) -> dict[str, str]:
    if not promote_possible_link(driver, link_id, _database()):
        raise HTTPException(status_code=409, detail="possible link not found or already definite")
    return {"linkId": link_id, "status": "definite"}
