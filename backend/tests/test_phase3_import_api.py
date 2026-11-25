from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from neo4j import GraphDatabase

from app import graph_schema
from app.coordinates import convert_to_latlong
from app.import_data import (
    FIELDS,
    infer_possible_links,
    load_source,
    parse_date,
    parse_record,
    read_records,
)
from app.main import app, get_driver


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("660520", date(1966, 5, 20)),
        ("65182", date(1965, 7, 1)),
        ("68229", date(1968, 8, 16)),
        ("73100J", date(1973, 4, 10)),
        ("1969-12-31", date(1969, 12, 31)),
    ],
)
def test_parse_date_normalizes_calendar_and_julian_values(raw: str, expected: date) -> None:
    assert parse_date(raw) == expected


@pytest.mark.parametrize("year_suffix", range(65, 74))
def test_julian_date_parser_covers_supported_years(year_suffix: int) -> None:
    year = 1900 + year_suffix
    assert parse_date(f"{year_suffix:02d}001") == date(year, 1, 1)
    assert parse_date(f"{year_suffix:02d}001J") == date(year, 1, 1)


@pytest.mark.parametrize("raw", [None, "", "   ", "74001", "660366", "660231", "1964-05-20", "72100JX"])
def test_parse_date_ignores_missing_invalid_or_out_of_range_values(raw: str | None) -> None:
    assert parse_date(raw) is None


@pytest.mark.parametrize(
    ("gzd", "raw", "expected_lat", "expected_lon"),
    [
        ("48Q", "WH000114", 20.0, 105.0),
        ("49Q", "CC953117", 20.0, 110.0),
        ("48P", "WU000265", 12.0, 105.0),
        ("49P", "CP911267", 12.0, 110.0),
    ],
)
def test_convert_to_latlong_selects_correct_vietnam_gzd(
    gzd: str, raw: str, expected_lat: float, expected_lon: float
) -> None:
    converted = convert_to_latlong(raw.lower())
    assert converted is not None
    assert converted.gzd == gzd
    assert converted.mgrs == f"{gzd}{raw}"
    assert converted.latitude == pytest.approx(expected_lat, abs=0.01)
    assert converted.longitude == pytest.approx(expected_lon, abs=0.01)


@pytest.mark.parametrize("raw", [None, "", "bad-value", "ZZ999999", "AA000000"])
def test_convert_to_latlong_returns_none_for_missing_or_invalid_utm(raw: str | None) -> None:
    assert convert_to_latlong(raw) is None


def make_line(values: dict[str, str]) -> str:
    line = [" "] * 298
    for name, value in values.items():
        start, end, _ = FIELDS[name]
        assert len(value) <= end - start
        line[start:end] = list(value.ljust(end - start))
    return "".join(line)


def test_parse_record_maps_all_fields_dates_utm_units_and_control_group(tmp_path: Path) -> None:
    source = tmp_path / "SITRA.TR.6668.txt"
    line = make_line({
        "DATE": "660520", "DATAT": "W", "SERAL": "003", "CORP": "1", "PART": "A",
        "OPNAM": "Junction City", "OPCOD": "A1", "UDATE": "67125",
        "PRVC1": "01", "UTM": "WH000114", "FSLIN": "001", "CONAM": "Task Force",
        "SSLIN": "001", "TYPAT": "AA", "OBJEC": "01", "OBJDS": "VC",
        "LINFS": "001", "SVNAT": "V", "COMPY": "A01", "BNID": "1 BN",
    })

    record = parse_record(line, source, 17)

    assert record is not None
    assert record["report"]["recordId"] == "SITRA.TR.6668.txt:17"
    assert record["report"]["reportDate"] == date(1966, 5, 20)
    assert record["report"]["reportDateRaw"] == "660520"
    assert record["report"]["sourceMgrs"] == "48QWH000114"
    assert record["report"]["latitude"] == pytest.approx(20.0, abs=0.01)
    assert record["fixed"]["updateDate"] == date(1967, 5, 5)
    assert record["fixed"]["updateDateRaw"] == "67125"
    assert record["sourceGroup"]["messageSentDate"] == date(1966, 5, 20)
    assert record["periodicSets"][1]["properties"]["kind"] == "Action"
    assert record["periodicSets"][2]["unit"]["company"] == "A01"
    assert "Junction City" in record["report"]["searchText"]
    assert all(value in record["report"]["searchText"] for value in ["Task Force", "VC", "1 BN"])


def test_search_text_includes_each_imported_source_field(tmp_path: Path) -> None:
    source = tmp_path / "all-fields.txt"
    for index, (name, (start, end, _group)) in enumerate(FIELDS.items()):
        token = chr(ord("A") + (index % 26)) * (end - start)
        record = parse_record(make_line({name: token}), source, index + 1)
        assert record is not None
        assert token.strip() in record["report"]["searchText"]


def test_parse_record_preserves_records_with_invalid_date_or_coordinate(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    record = parse_record(make_line({"DATE": "74001", "UTM": "XX999999"}), source, 1)

    assert record is not None
    assert "reportDate" not in record["report"]
    assert record["report"]["reportDateRaw"] == "74001"
    assert "latitude" not in record["report"]
    assert record["report"]["sourceUtm"] == "XX999999"


def test_read_records_counts_malformed_rows_and_keeps_valid_rows(tmp_path: Path) -> None:
    source = tmp_path / "sample.txt"
    source.write_bytes((make_line({"DATE": "660520"}) + "\r\nshort\r\n").encode("ascii"))
    records, counts = read_records(source)

    loaded = list(records)
    assert len(loaded) == 1
    assert counts == {"read": 2, "skipped": 1, "withoutDate": 0, "withoutCoordinates": 1}


def test_load_source_writes_records_in_batches(tmp_path: Path) -> None:
    source = tmp_path / "sample.txt"
    source.write_bytes((make_line({"DATE": "660520"}) + "\n" + make_line({"DATE": "660521"}) + "\n").encode())
    session = MagicMock()
    session.__enter__.return_value = session
    session.execute_write.side_effect = lambda _callback, rows: len(rows)
    driver = MagicMock()
    driver.session.return_value = session

    counts = load_source(driver, source, batch_size=1)

    assert counts["loaded"] == 2
    assert session.execute_write.call_count == 2


def test_import_and_inferred_links_against_neo4j(tmp_path: Path) -> None:
    uri = graph_schema.os.getenv("NEO4J_URI", "bolt://localhost:7687")
    database = graph_schema.os.getenv("NEO4J_DATABASE", "neo4j")
    source = tmp_path / "phase3-loader-check.txt"
    row = make_line({
        "DATE": "660520", "DATAT": "W", "SERAL": "ZZZ", "CORP": "Z", "PART": "Z",
        "UTM": "WH000114", "LINFS": "001", "SVNAT": "V", "COMPY": "XQ3", "BNID": "PH3TEST",
    })
    source.write_bytes((row + "\r\n" + row + "\r\n").encode("ascii"))
    driver = GraphDatabase.driver(uri)
    graph_schema.apply_schema(driver, database)
    try:
        counts = load_source(driver, source, database, batch_size=1)
        infer_possible_links(driver, database, [source.name])
        with driver.session(database=database) as session:
            result = session.run(
                """
                MATCH (report:Report {sourceFile: $source})
                OPTIONAL MATCH (report)-[:MEMBER_OF]->(group:SourceGroup)
                OPTIONAL MATCH (report)-[:HAS_FIXED_SET]->(:FixedSet)-[:HAS_PERIODIC_SET]->(periodic:PeriodicSet)
                RETURN count(DISTINCT report) AS reports,
                       count(DISTINCT group) AS groups,
                       count(DISTINCT periodic) AS periodicSets,
                       collect(DISTINCT report.reportDateRaw) AS rawDates,
                       collect(DISTINCT report.sourceMgrs) AS mgrsValues
                """,
                source=source.name,
            ).single()
            link = session.run(
                """
                MATCH (a:Report {sourceFile: $source})-[link:RELATED_TO]->(b:Report {sourceFile: $source})
                RETURN link.status AS status, link.evidence AS evidence
                """,
                source=source.name,
            ).single()
            weekly_reports = session.run(
                "MATCH (report:Report:WeeklySummary {sourceFile: $source}) RETURN count(report) AS count",
                source=source.name,
            ).single()["count"]
        assert counts["loaded"] == 2
        assert result["reports"] == 2
        assert result["groups"] == 1
        assert result["periodicSets"] == 4
        assert weekly_reports == 2
        assert result["rawDates"] == ["660520"]
        assert result["mgrsValues"] == ["48QWH000114"]
        assert link["status"] == "possible"
        assert {"shared_date:1966-05-20", "shared_place:48QWH000114"}.issubset(set(link["evidence"]))
        assert any(value.startswith("shared_unit:") for value in link["evidence"])
    finally:
        with driver.session(database=database) as session:
            session.run(
                "MATCH (report:Report {sourceFile: $source}) DETACH DELETE report",
                source=source.name,
            ).consume()
            session.run(
                "MATCH (node) WHERE node.sourceFile = $source DETACH DELETE node",
                source=source.name,
            ).consume()
            session.run(
                "MATCH (group:SourceGroup {sourceControlValues: $values}) DETACH DELETE group",
                values="|".join(("660520", "W", "ZZZ", "Z", "Z")),
            ).consume()
            session.run(
                "MATCH (unit:Unit {company: 'XQ3', battalionId: 'PH3TEST'}) DETACH DELETE unit"
            ).consume()
        driver.close()


def test_api_search_validation_and_health() -> None:
    client = TestClient(app)
    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.get("/api/records?from=1970-01-02&to=1969-12-31").status_code == 422
    assert client.get("/api/records?limit=201").status_code == 422


def test_api_records_details_related_and_promotion_against_neo4j() -> None:
    uri = graph_schema.os.getenv("NEO4J_URI", "bolt://localhost:7687")
    database = graph_schema.os.getenv("NEO4J_DATABASE", "neo4j")
    tag = "phase3-api-integration"
    record_a, record_b, record_c = (f"{tag}:{name}" for name in ("a", "b", "c"))
    link_id = graph_schema.related_link_id(record_a, record_c)
    driver = GraphDatabase.driver(uri)
    graph_schema.apply_schema(driver, database)
    with driver.session(database=database) as session:
        session.run(
            """
            MERGE (a:Report {recordId: $a})
            SET a += {phase3Sample: $tag, reportDate: date('1968-01-03'), searchText: 'phase3jungle example one', sourceMgrs: '48QWH000114', latitude: 20.0, longitude: 105.0}
            MERGE (b:Report {recordId: $b})
            SET b += {phase3Sample: $tag, reportDate: date('1968-01-03'), searchText: 'phase3jungle example two'}
            MERGE (c:Report {recordId: $c})
            SET c += {phase3Sample: $tag, reportDate: date('1968-01-04'), searchText: 'phase3jungle example three'}
            MERGE (group:SourceGroup {groupKey: $group_key})
            SET group += {phase3Sample: $tag, messageSentDate: date('1968-01-03'), reportType: 'W', paragraphNumber: '003', militaryRegion: '1', part: 'A'}
            MERGE (a)-[:MEMBER_OF]->(group)
            MERGE (b)-[:MEMBER_OF]->(group)
            MERGE (a)-[link:RELATED_TO {linkId: $link_id}]->(c)
            SET link.status = 'possible', link.origin = 'metadata_inferred', link.evidence = ['shared_unit:phase3-test-unit', 'shared_date:1968-01-04']
            MERGE (fixed:FixedSet {fixedSetId: $fixed_id})
            SET fixed += {phase3Sample: $tag}
            MERGE (c)-[:HAS_FIXED_SET]->(fixed)
            MERGE (periodic:PeriodicSet {periodicSetId: $periodic_id})
            SET periodic += {phase3Sample: $tag, kind: 'Unit', svnat: 'V'}
            MERGE (fixed)-[:HAS_PERIODIC_SET]->(periodic)
            """,
            a=record_a,
            b=record_b,
            c=record_c,
            tag=tag,
            group_key=f"{tag}:group",
            link_id=link_id,
            fixed_id=f"{tag}:fixed",
            periodic_id=f"{tag}:periodic",
        ).consume()

    app.dependency_overrides[get_driver] = lambda: driver
    client = TestClient(app)
    try:
        first_page = client.get("/api/records", params={"q": "phase3jungle", "from": "1968-01-01", "to": "1968-01-03", "limit": 2})
        assert first_page.status_code == 200
        assert first_page.json()["total"] == 2
        assert len(first_page.json()["items"]) == 2

        second_page = client.get("/api/records", params={"q": "phase3jungle", "offset": 2, "limit": 2})
        assert second_page.json()["total"] == 3
        assert len(second_page.json()["items"]) == 1

        detail = client.get(f"/api/records/{record_c}")
        assert detail.status_code == 200
        assert detail.json()["record"]["recordId"] == record_c
        assert detail.json()["periodicSets"][0]["kind"] == "Unit"
        map_result = client.get("/api/records", params={"q": "phase3jungle", "limit": 10}).json()
        map_record = next(item["record"] for item in map_result["items"] if item["record"]["recordId"] == record_a)
        assert map_record["latitude"] == 20.0
        assert map_record["longitude"] == 105.0

        related = client.get(f"/api/records/{record_a}/related").json()["items"]
        assert {item["status"] for item in related} == {"definite", "possible"}
        possible = next(item for item in related if item["status"] == "possible")
        assert "shared_unit:phase3-test-unit" in possible["evidence"]

        promoted = client.post(f"/api/links/{link_id}/promote")
        assert promoted.status_code == 200
        assert promoted.json()["status"] == "definite"
        assert client.post(f"/api/links/{link_id}/promote").status_code == 409
        assert client.get("/api/records/missing-record").status_code == 404
    finally:
        app.dependency_overrides.pop(get_driver, None)
        with driver.session(database=database) as session:
            session.run("MATCH (node {phase3Sample: $tag}) DETACH DELETE node", tag=tag).consume()
        driver.close()
