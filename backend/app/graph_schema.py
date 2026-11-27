import argparse
import os
from pathlib import Path
from typing import Any

from neo4j import Driver, GraphDatabase

SCHEMA_FILE = Path(__file__).parents[1] / "cypher" / "schema.cypher"
SAMPLE_TAG = "phase2-schema-demo"
RECORD_A = "__phase2_demo__:record-a"
RECORD_B = "__phase2_demo__:record-b"
RECORD_C = "__phase2_demo__:record-c"
SOURCE_GROUP = "__phase2_demo__:source-group"
SAMPLE_LINK = "__phase2_demo__:possible-link"

SAMPLE_QUERY = """
MERGE (large:Report:LargeScaleOperation {recordId: $record_a})
SET large += {
    sampleRun: $sample_tag,
    reportDate: date('1968-01-03'),
    reportType: 'LARGE',
    serial: 'DEMO-01',
    militaryRegion: 'DEMO-I',
    part: 'A',
    sourceUtm: 'DEMO-UTM',
    mgrsGzd: '48Q',
    sourceMgrs: 'DEMO-MGRS',
    latitude: 16.8,
    longitude: 107.0,
    searchText: 'sample large operation with unit and province evidence'
}
MERGE (small:Report:SmallScaleOperation {recordId: $record_b})
SET small += {
    sampleRun: $sample_tag,
    reportDate: date('1968-01-03'),
    reportType: 'SMALL',
    serial: 'DEMO-01',
    militaryRegion: 'DEMO-I',
    part: 'A',
    searchText: 'sample small operation in source control group'
}
MERGE (related:Report:SmallScaleOperation {recordId: $record_c})
SET related += {
    sampleRun: $sample_tag,
    reportDate: date('1968-01-03'),
    reportType: 'SMALL',
    serial: 'DEMO-02',
    militaryRegion: 'DEMO-I',
    part: 'A',
    searchText: 'sample related operation sharing a unit and province'
}

MERGE (sourceGroup:SourceGroup {groupKey: $source_group})
SET sourceGroup += {
    sampleRun: $sample_tag,
    messageSentDate: date('1968-01-03'),
    reportType: 'LARGE',
    paragraphNumber: 'DEMO-01',
    militaryRegion: 'DEMO-I',
    part: 'A'
}
MERGE (large)-[:MEMBER_OF]->(sourceGroup)
MERGE (small)-[:MEMBER_OF]->(sourceGroup)

MERGE (province:Province {code: '__phase2_demo__:province'})
SET province += {sampleRun: $sample_tag, description: 'Sample Province'}
MERGE (unit:Unit {unitKey: '__phase2_demo__:unit'})
SET unit += {sampleRun: $sample_tag, svnat: 'SAMPLE', compy: '01'}

UNWIND [
    {record: large, fixedSetId: '__phase2_demo__:fixed-a', periodicSetId: '__phase2_demo__:periodic-a'},
    {record: small, fixedSetId: '__phase2_demo__:fixed-b', periodicSetId: '__phase2_demo__:periodic-b'},
    {record: related, fixedSetId: '__phase2_demo__:fixed-c', periodicSetId: '__phase2_demo__:periodic-c'}
] AS row
WITH row.record AS report, row.fixedSetId AS fixedSetId,
     row.periodicSetId AS periodicSetId, unit, province, large, related
MERGE (fixedSet:FixedSet {fixedSetId: fixedSetId})
SET fixedSet += {sampleRun: $sample_tag, updateDate: date('1968-01-05')}
MERGE (report)-[:HAS_FIXED_SET]->(fixedSet)
MERGE (periodicSet:PeriodicSet {periodicSetId: periodicSetId})
SET periodicSet += {sampleRun: $sample_tag, setNumber: 3, lineNumber: '01', kind: 'Unit'}
MERGE (report)-[:HAS_PERIODIC_SET]->(periodicSet)
MERGE (periodicSet)-[:HAS_UNIT]->(unit)
MERGE (fixedSet)-[:HAS_PRIMARY_PROVINCE]->(province)

WITH large, related
MERGE (large)-[link:RELATED_TO {linkId: $link_id}]->(related)
SET link.status = 'possible',
    link.origin = 'metadata_inferred',
    link.evidence = [
        'shared_unit:__phase2_demo__:unit',
        'shared_place:__phase2_demo__:province',
        'shared_date:1968-01-03'
    ]
"""

PROMOTE_QUERY = """
MATCH (:Report)-[link:RELATED_TO {
    linkId: $link_id,
    status: 'possible',
    origin: 'metadata_inferred'
}]->(:Report)
SET link.status = 'definite',
    link.confirmedAt = datetime(),
    link.confirmedBy = 'user_action'
RETURN link.linkId AS linkId
"""


def schema_statements(path: Path = SCHEMA_FILE) -> list[str]:
    return [statement.strip() for statement in path.read_text().split(";") if statement.strip()]


def related_link_id(record_id_a: str, record_id_b: str) -> str:
    first, second = sorted((record_id_a.encode("utf-8"), record_id_b.encode("utf-8")))
    if first == second:
        raise ValueError("a report cannot be linked to itself")
    return f"related:{first.decode('utf-8')}|{second.decode('utf-8')}"


def apply_schema(driver: Driver, database: str = "neo4j") -> None:
    with driver.session(database=database) as session:
        for statement in schema_statements():
            session.run(statement).consume()


def _query_one(driver: Driver, query: str, database: str = "neo4j", **parameters: Any) -> dict[str, Any] | None:
    with driver.session(database=database) as session:
        record = session.run(query, parameters).single()
        return record.data() if record else None


def _cleanup_sample(tx: Any) -> None:
    tx.run("MATCH (node {sampleRun: $tag}) DETACH DELETE node", tag=SAMPLE_TAG).consume()


def create_sample_graph(driver: Driver, database: str = "neo4j") -> None:
    with driver.session(database=database) as session:
        session.execute_write(_cleanup_sample)
        session.run(
            SAMPLE_QUERY,
            record_a=RECORD_A,
            record_b=RECORD_B,
            record_c=RECORD_C,
            source_group=SOURCE_GROUP,
            link_id=SAMPLE_LINK,
            sample_tag=SAMPLE_TAG,
        ).consume()


def cleanup_sample_graph(driver: Driver, database: str = "neo4j") -> None:
    with driver.session(database=database) as session:
        session.execute_write(_cleanup_sample)


def promote_possible_link(driver: Driver, link_id: str, database: str = "neo4j") -> bool:
    return _query_one(driver, PROMOTE_QUERY, database, link_id=link_id) is not None


def validate_sample_graph(driver: Driver, database: str = "neo4j") -> dict[str, Any]:
    create_sample_graph(driver, database)
    try:
        source_link = _query_one(
            driver,
            """
            MATCH (:Report {recordId: $record_a})-[:MEMBER_OF]->(group:SourceGroup)
                  <-[:MEMBER_OF]-(:Report {recordId: $record_b})
            RETURN group.messageSentDate AS messageSentDate,
                   group.reportType AS reportType,
                   group.paragraphNumber AS paragraphNumber,
                   group.militaryRegion AS militaryRegion,
                   group.part AS part
            """,
            database,
            record_a=RECORD_A,
            record_b=RECORD_B,
        )
        if source_link is None:
            raise AssertionError("sample source-stated record group was not traversable")

        map_fields = _query_one(
            driver,
            """
            MATCH (report:Report {recordId: $record_a})
            RETURN report.sourceUtm AS sourceUtm, report.mgrsGzd AS mgrsGzd,
                   report.sourceMgrs AS sourceMgrs, report.latitude AS latitude,
                   report.longitude AS longitude
            """,
            database,
            record_a=RECORD_A,
        )
        if (
            map_fields is None
            or map_fields["sourceUtm"] != "DEMO-UTM"
            or map_fields["mgrsGzd"] != "48Q"
            or map_fields["sourceMgrs"] != "DEMO-MGRS"
            or map_fields["latitude"] is None
            or map_fields["longitude"] is None
        ):
            raise AssertionError("source grid values and normalized coordinates were not retained")

        source_and_periodic_sets = _query_one(
            driver,
            """
            MATCH (report:Report {sampleRun: $sample_tag})
                  -[:HAS_PERIODIC_SET]->(:PeriodicSet)
                  -[:HAS_UNIT]->(:Unit)
            RETURN count(DISTINCT report) AS count
            """,
            database,
            sample_tag=SAMPLE_TAG,
        )
        if source_and_periodic_sets is None or source_and_periodic_sets["count"] != 3:
            raise AssertionError("sample ontology records or unit traversal did not match")

        date_filter = _query_one(
            driver,
            """
            MATCH (report:Report)
            WHERE report.sampleRun = $sample_tag
              AND report.reportDate >= date('1968-01-01')
              AND report.reportDate <= date('1968-01-31')
            RETURN count(report) AS count
            """,
            database,
            sample_tag=SAMPLE_TAG,
        )
        if date_filter is None or date_filter["count"] != 3:
            raise AssertionError("report date filtering did not return the sample records")

        text_search = _query_one(
            driver,
            """
            MATCH (report:Report)
            SEARCH report IN (
                FULLTEXT INDEX report_search
                FOR $term
                LIMIT 3000000
            )
            SCORE AS score
            WHERE report.sampleRun = $sample_tag
            RETURN count(report) AS count
            """,
            database,
            term="operation",
            sample_tag=SAMPLE_TAG,
        )
        if text_search is None or text_search["count"] != 3:
            raise AssertionError("sample full-text index did not find the report text")

        before = _query_one(
            driver,
            """
            MATCH (:Report)-[link:RELATED_TO {linkId: $link_id}]->(:Report)
            RETURN link.status AS status, link.origin AS origin, link.evidence AS evidence
            """,
            database,
            link_id=SAMPLE_LINK,
        )
        if before is None or before["status"] != "possible":
            raise AssertionError("sample inferred association was not labeled possible")

        promoted = promote_possible_link(driver, SAMPLE_LINK, database)
        duplicate_promotion = promote_possible_link(driver, SAMPLE_LINK, database)
        after = _query_one(
            driver,
            """
            MATCH (:Report)-[link:RELATED_TO {linkId: $link_id}]->(:Report)
            RETURN link.status AS status, link.origin AS origin,
                   link.evidence AS evidence, link.confirmedAt IS NOT NULL AS confirmed
            """,
            database,
            link_id=SAMPLE_LINK,
        )
        if (
            not promoted
            or duplicate_promotion
            or after is None
            or after["status"] != "definite"
            or after["origin"] != before["origin"]
            or after["evidence"] != before["evidence"]
            or not after["confirmed"]
        ):
            raise AssertionError("link promotion changed or lost its inference evidence")

        return {
            "sourceControlGroup": source_link,
            "recordsInDateRange": date_filter["count"],
            "possibleLinkEvidence": before["evidence"],
            "promotedStatus": after["status"],
            "evidenceRetained": after["evidence"] == before["evidence"],
        }
    finally:
        cleanup_sample_graph(driver, database)


def main() -> None:
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
