from typing import Any

from neo4j import Driver

from app import graph_schema as graph

SAMPLE_TAG = "phase2-canonical-sitra-demo"
RECORD_A = "680103L~01  "
UNIT_MATCH = "680110S~0211"
PLACE_MATCH = "680110E~0311"
TOO_LATE = "680111S~0411"
SUMMARY = "680103W~0511"

SEED_RECORDS = """
CREATE (a:DataRecord:LargeScaleOperation {dataRecordId: $a, sampleRun: $tag,
    DATE: '680103', DATAT: 'L', SERAL: '~01', CORP: ' ', PART: ' ',
    reportDate: date('1968-01-03'), OPNAM: 'Sample Operation', searchText: 'sample operation'})
CREATE (b:DataRecord:SmallScaleOperation {dataRecordId: $b, sampleRun: $tag,
    reportDate: date('1968-01-10'), searchText: 'sample action'})
CREATE (c:DataRecord:EnemyInitiated {dataRecordId: $c, sampleRun: $tag,
    reportDate: date('1968-01-10'), searchText: 'sample incident'})
CREATE (late:DataRecord:SmallScaleOperation {dataRecordId: $late, sampleRun: $tag,
    reportDate: date('1968-01-11'), searchText: 'sample action'})
CREATE (summary:DataRecord:WeeklySummary {dataRecordId: $summary, sampleRun: $tag,
    reportDate: date('1968-01-03'), searchText: 'sample summary'})
CREATE (a)-[:REPORTS]->(:Event:Operation {eventId: $tag + ':operation', sampleRun: $tag})
CREATE (b)-[:REPORTS]->(:Event:Action {eventId: $tag + ':action', sampleRun: $tag})
CREATE (c)-[:REPORTS]->(:Event:EnemyIncident {eventId: $tag + ':incident', sampleRun: $tag})
CREATE (unit:Unit:Battalion {unitKey: $tag + ':unit', resolved: true, sampleRun: $tag})
CREATE (unknown:Unit {unitKey: $tag + ':unknown', resolved: false, sampleRun: $tag})
CREATE (province:Location:Province {locationKey: $tag + ':province', specific: true, sampleRun: $tag})
CREATE (country:Location:Country {locationKey: $tag + ':country', specific: true, sampleRun: $tag})
CREATE (province)-[:IN_COUNTRY]->(country)
CREATE (a)-[:REFERENCES_UNIT]->(unit), (b)-[:REFERENCES_UNIT]->(unit), (late)-[:REFERENCES_UNIT]->(unit)
CREATE (a)-[:REFERENCES_UNIT]->(unknown), (summary)-[:REFERENCES_UNIT]->(unknown)
CREATE (a)-[:REPORTS_GEOGRAPHY {sourceField: 'PRVC1', rank: 1}]->(province)
CREATE (c)-[:REPORTS_GEOGRAPHY]->(province)
CREATE (a)-[:REPORTS_GEOGRAPHY]->(country), (summary)-[:REPORTS_GEOGRAPHY]->(country)
"""

SEED_OCCURRENCES = """
UNWIND $rows AS row
MATCH (record:DataRecord {dataRecordId: row.recordId})
CREATE (record)-[:HAS_PERIODIC_SET]->(occurrence:PeriodicSet {
    periodicSetId: $tag + ':' + toString(row.setNumber) + ':' + toString(row.sourceRow),
    sampleRun: $tag, sourceFile: 'synthetic-sitra.dat'
})
SET occurrence += row.properties, occurrence.setNumber = row.setNumber,
    occurrence.sourceRow = row.sourceRow
"""

SEED_MATERIALS = """
CREATE (:Material:Weapon {materialKey: $tag + ':01', kind: 'Weapon', name: 'Small arms', sampleRun: $tag})
CREATE (:Material:Ammunition {materialKey: $tag + ':AC', kind: 'Ammunition', name: 'Small arms rounds', sampleRun: $tag})
CREATE (:Material:Provision {materialKey: $tag + ':G0', kind: 'Provision', name: 'Medical supplies', sampleRun: $tag})
WITH $tag AS tag
MATCH (row:PeriodicSet {sampleRun: tag, setNumber: 4}), (material:Material {sampleRun: tag})
WHERE material.materialKey = tag + ':' + row.LSCAT + row.LSCLS
CREATE (row)-[:ABOUT]->(material)
"""

OCCURRENCES = [
    (RECORD_A, 1, 1, {"FSLIN": "001", "NGFS": "999"}),
    (RECORD_A, 2, 1, {"SSLIN": "001", "UTM": "YD123456", "coordinateStatus": "verified",
                       "mgrsGzd": "48Q", "sourceMgrs": "48QYD123456", "latitude": 16.6, "longitude": 107.0}),
    (RECORD_A, 2, 2, {"SSLIN": "002", "UTM": "YD124456", "coordinateStatus": "verified",
                       "mgrsGzd": "48Q", "sourceMgrs": "48QYD124456", "latitude": 16.6, "longitude": 107.001}),
    (RECORD_A, 2, 3, {"SSLIN": "003", "UTM": "AA123456", "coordinateStatus": "ambiguous"}),
    (RECORD_A, 3, 1, {"LINFS": "001", "BNID": "SAMPLE BN", "MVRSP": "M"}),
    (RECORD_A, 4, 1, {"TSLIN": "2B1", "LSCAT": "0", "LSCLS": "1", "NODES": "00002", "LUNIT": "EA "}),
    (RECORD_A, 4, 2, {"TSLIN": "2B1", "LSCAT": "A", "LSCLS": "C", "NODAM": "00001", "LUNIT": "EA "}),
    (RECORD_A, 4, 3, {"TSLIN": "2B2", "LSCAT": "G", "LSCLS": "0"}),
    (RECORD_A, 4, 4, {"TSLIN": "2B3", "LSCAT": "?", "LSCLS": "?"}),
    (SUMMARY, 4, 5, {"TSLIN": "001", "LSCAT": "0", "LSCLS": "1"}),
    (SUMMARY, 5, 5, {"SFLIN": "001", "IACTS": "00007"}),
    (SUMMARY, 6, 5, {"LINSS": "001", "RTWER": "0123"}),
    (SUMMARY, 7, 5, {"SLINS": "001", "LCTZ1": "0001"}),
]


def _seed(tx: Any) -> None:
    tx.run(SEED_RECORDS, tag=SAMPLE_TAG, a=RECORD_A, b=UNIT_MATCH, c=PLACE_MATCH,
           late=TOO_LATE, summary=SUMMARY).consume()
    tx.run(SEED_OCCURRENCES, tag=SAMPLE_TAG, rows=[
        dict(recordId=record, setNumber=number, sourceRow=row, properties=props)
        for record, number, row, props in OCCURRENCES
    ]).consume()
    tx.run(SEED_MATERIALS, tag=SAMPLE_TAG).consume()
    tx.run("""
        MATCH (record:DataRecord {dataRecordId: $record_id})-[:REPORTS]->(event:Event),
              (record)-[:REFERENCES_UNIT]->(unit:Unit {resolved: true}),
              (record)-[:HAS_PERIODIC_SET]->(participation:PeriodicSet {setNumber: 3})
        CREATE (unit)-[:PARTICIPATED_IN {periodicSetId: participation.periodicSetId}]->(event)
        WITH record, event
        MATCH (record)-[:HAS_PERIODIC_SET]->(objective:PeriodicSet {setNumber: 2})
        CREATE (event)-[:HAS_OBJECTIVE_LOCATION]->(:Location:ObjectiveGrid {
          locationKey: objective.periodicSetId, UTM: objective.UTM, sampleRun: $tag
        })
        """, record_id=RECORD_A, tag=SAMPLE_TAG).consume()


def cleanup_sample_graph(driver: Driver, database: str = "neo4j") -> None:
    with driver.session(database=database) as session:
        session.run("MATCH (node {sampleRun: $tag}) DETACH DELETE node", tag=SAMPLE_TAG).consume()


def validate_sample_graph(driver: Driver, database: str = "neo4j") -> dict[str, Any]:
    with driver.session(database=database) as session:
        session.execute_write(_seed)
    try:
        source = graph._rows(driver, """
            MATCH (record:DataRecord {dataRecordId: $record_id})-[:REPORTS]->(event:Event:Operation)
                  <-[:PARTICIPATED_IN]-(:Unit:Battalion),
                  (record)-[:REPORTS_GEOGRAPHY]->(:Location:Province)-[:IN_COUNTRY]->(:Location:Country),
                  (record)-[:HAS_PERIODIC_SET]->(loss:PeriodicSet {setNumber: 4, TSLIN: '2B1'})
            RETURN count(DISTINCT event) AS events, count(DISTINCT loss) AS repeatedLineOccurrences
            """, database, record_id=RECORD_A)[0]
        assert source == {"events": 1, "repeatedLineOccurrences": 2}

        points = graph.record_map_points(driver, RECORD_A, database)
        assert [p["sourceUtm"] for p in points] == ["YD123456", "YD124456"]
        materials = graph.record_material_network(driver, RECORD_A, database)
        assert {m["kind"] for m in materials} == {"Weapon", "Ammunition", "Provision"}
        assert next(m for m in materials if m["kind"] == "Weapon")["otherRecordIds"] == [SUMMARY]

        assert graph.infer_record_links(driver, RECORD_A, database) == 2
        query = """
            MATCH (:DataRecord {dataRecordId: $record_id})-[link:RELATED_TO]-(other:DataRecord)
            RETURN other.dataRecordId AS otherId, link.linkId AS linkId, link.status AS status,
                   link.origin AS origin, link.evidence AS evidence, link.daysApart AS daysApart,
                   link.confirmedBy AS confirmedBy
        """
        before = {item["otherId"]: item for item in graph._rows(driver, query, database, record_id=RECORD_A)}
        assert set(before) == {UNIT_MATCH, PLACE_MATCH}
        assert before[UNIT_MATCH]["evidence"] == [f"shared_unit:{SAMPLE_TAG}:unit"]
        assert before[PLACE_MATCH]["evidence"] == [f"shared_place:{SAMPLE_TAG}:province"]
        assert all(item["status"] == "possible" and item["daysApart"] == 7 for item in before.values())
        link_id = before[UNIT_MATCH]["linkId"]
        assert graph.promote_possible_link(driver, link_id, database)
        assert not graph.promote_possible_link(driver, link_id, database)
        graph.infer_record_links(driver, UNIT_MATCH, database)
        after = {item["otherId"]: item for item in graph._rows(driver, query, database, record_id=RECORD_A)}
        assert after[UNIT_MATCH] == (before[UNIT_MATCH] | {"status": "definite", "confirmedBy": "user_action"})

        search = graph._rows(driver, """
            CALL db.index.fulltext.queryNodes('data_record_search', 'sample') YIELD node
            WHERE node.sampleRun = $tag AND node.reportDate >= date('1968-01-03')
              AND node.reportDate <= date('1968-01-10')
            RETURN count(node) AS count
            """, database, tag=SAMPLE_TAG)[0]
        assert search["count"] == 4
        return {"recordsInDateRange": search["count"], "repeatedLineOccurrences": 2,
                "verifiedMapPoints": len(points), "materialKinds": sorted(m["kind"] for m in materials),
                "promotedStatus": after[UNIT_MATCH]["status"], "evidenceRetained": True}
    finally:
        cleanup_sample_graph(driver, database)
