import argparse
import hashlib
import os
from pathlib import Path
from typing import Any

from neo4j import Driver, GraphDatabase

SCHEMA_FILE = Path(__file__).parents[1] / "cypher" / "schema.cypher"

INFERENCE_CANDIDATES = """
MATCH (record:DataRecord {dataRecordId: $record_id})
CALL (record) {
    MATCH (record)-[:REFERENCES_UNIT]->(unit:Unit {resolved: true})
          <-[:REFERENCES_UNIT]-(other:DataRecord)
    RETURN other, 'shared_unit:' + unit.unitKey AS evidence
    UNION
    MATCH (record)-[:REPORTS_GEOGRAPHY]->(place:Location {specific: true})
          <-[:REPORTS_GEOGRAPHY]-(other:DataRecord)
    WHERE NOT place:Country
    RETURN other, 'shared_place:' + place.locationKey AS evidence
}
WITH record, other, evidence
WHERE record <> other
  AND other.reportDate >= record.reportDate - duration({days: 7})
  AND other.reportDate <= record.reportDate + duration({days: 7})
RETURN other.dataRecordId AS otherId, collect(DISTINCT evidence) AS evidence,
       abs(duration.inDays(record.reportDate, other.reportDate).days) AS daysApart
"""

MERGE_INFERRED_LINKS = """
UNWIND $links AS row
MATCH (first:DataRecord {dataRecordId: row.first}),
      (second:DataRecord {dataRecordId: row.second})
MERGE (first)-[link:RELATED_TO {linkId: row.linkId}]->(second)
ON CREATE SET link.status = 'possible', link.origin = 'metadata_inferred'
SET link.evidence = CASE link.status WHEN 'possible' THEN row.evidence ELSE link.evidence END,
    link.daysApart = CASE link.status WHEN 'possible' THEN row.daysApart ELSE link.daysApart END
"""

PROMOTE_QUERY = """
MATCH (:DataRecord)-[link:RELATED_TO {linkId: $link_id}]->(:DataRecord)
// Acquire a write lock before checking status so concurrent confirmations cannot both succeed.
SET link.status = link.status
WITH link WHERE link.status = 'possible' AND link.origin = 'metadata_inferred'
SET link.status = 'definite', link.confirmedAt = datetime(), link.confirmedBy = 'user_action'
RETURN link.linkId AS linkId
"""

MAP_POINTS_QUERY = """
MATCH (:DataRecord {dataRecordId: $record_id})-[:HAS_PERIODIC_SET]->
      (objective:PeriodicSet {setNumber: 2, coordinateStatus: 'verified'})
WHERE objective.latitude IS NOT NULL AND objective.longitude IS NOT NULL
RETURN objective.periodicSetId AS pointId, objective.UTM AS sourceUtm,
       objective.mgrsGzd AS mgrsGzd, objective.sourceMgrs AS sourceMgrs,
       objective.latitude AS latitude, objective.longitude AS longitude
ORDER BY objective.sourceRow, pointId
"""

MATERIAL_NETWORK_QUERY = """
MATCH (record:DataRecord {dataRecordId: $record_id})-[:HAS_PERIODIC_SET]->
      (:PeriodicSet {setNumber: 4})-[:ABOUT]->(material:Material)
WITH DISTINCT record, material
OPTIONAL MATCH (material)<-[:ABOUT]-(:PeriodicSet {setNumber: 4})
               <-[:HAS_PERIODIC_SET]-(other:DataRecord)
WHERE other <> record
RETURN material.materialKey AS materialKey, material.name AS name,
       material.kind AS kind, collect(DISTINCT other.dataRecordId) AS otherRecordIds
ORDER BY materialKey
"""


def schema_statements(path: Path = SCHEMA_FILE) -> list[str]:
    return [statement.strip() for statement in path.read_text().split(";") if statement.strip()]


def related_link_id(record_id_a: str, record_id_b: str) -> str:
    first, second = sorted((record_id_a.encode("utf-8"), record_id_b.encode("utf-8")))
    if first == second:
        raise ValueError("a record cannot be linked to itself")
    payload = len(first).to_bytes(4, "big") + first + len(second).to_bytes(4, "big") + second
    return "related:" + hashlib.sha256(payload).hexdigest()


def apply_schema(driver: Driver, database: str = "neo4j") -> None:
    with driver.session(database=database) as session:
        for statement in schema_statements():
            session.run(statement).consume()


def _rows(driver: Driver, query: str, database: str, **parameters: Any) -> list[dict[str, Any]]:
    with driver.session(database=database) as session:
        return session.run(query, parameters).data()


def _infer_links(tx: Any, record_id: str) -> int:
    links = []
    for candidate in tx.run(INFERENCE_CANDIDATES, record_id=record_id):
        first, second = sorted((record_id, candidate["otherId"]))
        links.append({
            "first": first, "second": second, "linkId": related_link_id(first, second),
            "evidence": sorted(candidate["evidence"]), "daysApart": candidate["daysApart"],
        })
    if links:
        tx.run(MERGE_INFERRED_LINKS, links=links).consume()
    return len(links)


def infer_record_links(driver: Driver, record_id: str, database: str = "neo4j") -> int:
    with driver.session(database=database) as session:
        return session.execute_write(_infer_links, record_id)


def promote_possible_link(driver: Driver, link_id: str, database: str = "neo4j") -> bool:
    return bool(_rows(driver, PROMOTE_QUERY, database, link_id=link_id))


def record_map_points(driver: Driver, record_id: str, database: str = "neo4j") -> list[dict[str, Any]]:
    return _rows(driver, MAP_POINTS_QUERY, database, record_id=record_id)


def record_material_network(driver: Driver, record_id: str, database: str = "neo4j") -> list[dict[str, Any]]:
    return _rows(driver, MATERIAL_NETWORK_QUERY, database, record_id=record_id)


def main() -> None:
    from app.graph_schema_sample import cleanup_sample_graph, validate_sample_graph

    parser = argparse.ArgumentParser(description="Set up or validate the SITRA Neo4j graph schema.")
    parser.add_argument("command", choices=("setup", "validate-sample", "cleanup-sample"))
    args = parser.parse_args()
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    database = os.getenv("NEO4J_DATABASE", "neo4j")

    with GraphDatabase.driver(uri) as driver:
        driver.verify_connectivity()
        if args.command == "setup":
            apply_schema(driver, database)
            print("Graph constraints and indexes are ready.")
        elif args.command == "validate-sample":
            apply_schema(driver, database)
            print(validate_sample_graph(driver, database))
        else:
            cleanup_sample_graph(driver, database)
            print("Phase 2 sample graph removed.")


if __name__ == "__main__":
    main()
