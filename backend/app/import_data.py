import argparse
import hashlib
import json
import os
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote

from neo4j import Driver, GraphDatabase

from app.code_values import code_label_fields, decode_code
from app.coordinates import convert_to_latlong
from app.graph_schema import apply_schema

RECORD_WIDTH = 298
BATCH_SIZE = 1000

# NARA's Translation File Record Layout, column positions expressed as [start, end).
FIELDS: dict[str, tuple[int, int, str]] = {
    "DATE": (0, 6, "control"), "DATAT": (6, 7, "control"),
    "SERAL": (7, 10, "control"), "CORP": (10, 11, "control"),
    "PART": (11, 12, "control"), "FNATL": (12, 13, "fixed"),
    "CNTRY": (13, 15, "fixed"), "OPNAM": (15, 40, "fixed"),
    "OPCOD": (40, 42, "fixed"), "UDATE": (42, 47, "fixed"),
    "PRVC1": (47, 49, "fixed"), "PRVC2": (49, 51, "fixed"),
    "PRVC3": (51, 53, "fixed"), "OPDAY": (53, 57, "fixed"),
    "CTDAY": (57, 58, "fixed"), "DTEI": (58, 64, "fixed"),
    "HOURT": (64, 68, "fixed"), "DTET": (68, 74, "fixed"),
    "HOURI": (74, 78, "fixed"), "FSLIN": (78, 81, "set1"),
    "CONAT": (81, 82, "set1"), "CONAM": (82, 97, "set1"),
    "NGFS": (97, 100, "set1"), "ARSVC": (100, 101, "set1"),
    "ARCFT": (101, 107, "set1"), "SSLIN": (107, 110, "set2"),
    "UTM": (110, 118, "set2"), "TYPAT": (118, 120, "set2"),
    "OBJEC": (120, 122, "set2"), "OBJDS": (122, 124, "set2"),
    "LINFS": (124, 127, "set3"), "SVNAT": (127, 128, "set3"),
    "NOOF": (128, 130, "set3"), "SMTH": (130, 131, "set3"),
    "COMPY": (131, 134, "set3"), "BNID": (134, 144, "set3"),
    "BRDES": (144, 154, "set3"), "DVDES": (154, 164, "set3"),
    "MVRSP": (164, 165, "set3"), "RESAC": (165, 166, "set3"),
    "TSLIN": (166, 169, "set4"), "LNATL": (169, 170, "set4"),
    "LSCAT": (170, 171, "set4"), "LSCLS": (171, 172, "set4"),
    "LSDSC": (172, 187, "set4"), "NODES": (187, 192, "set4"),
    "NODAM": (192, 197, "set4"), "NOCAP": (197, 202, "set4"),
    "LUNIT": (202, 205, "set4"), "SFLIN": (205, 208, "set5"),
    "INATL": (208, 209, "set5"), "ISIZE": (209, 210, "set5"),
    "IACTS": (210, 215, "set5"), "IWCTD": (215, 218, "set5"),
    "IWOCT": (218, 222, "set5"), "IATT": (222, 226, "set5"),
    "ITERR": (226, 230, "set5"), "ISABT": (230, 234, "set5"),
    "IPROP": (234, 238, "set5"), "IHARR": (238, 242, "set5"),
    "IAA": (242, 246, "set5"), "ICTZ": (246, 247, "set5"),
    "LINSS": (247, 250, "set6"), "RTWER": (250, 254, "set6"),
    "RTPER": (254, 258, "set6"), "RVNRR": (258, 264, "set6"),
    "RVNRL": (264, 270, "set6"), "RVNPR": (270, 276, "set6"),
    "SLINS": (276, 279, "set7"), "LNAT": (279, 280, "set7"),
    "LTYPE": (280, 281, "set7"), "LCTZ1": (281, 285, "set7"),
    "LCTZ2": (285, 289, "set7"), "LCTZ3": (289, 293, "set7"),
    "LCTZ4": (293, 297, "set7"), "LNATI": (297, 298, "set7"),
}

SET_KINDS = {
    "set1": "CombinedOperation", "set2": "Action", "set3": "Unit",
    "set4": "Loss", "set5": "Incidents", "set6": "RVNStats",
    "set7": "LossStats",
}
SET_LINE_FIELDS = {
    "set1": "FSLIN", "set2": "SSLIN", "set3": "LINFS",
    "set4": "TSLIN", "set5": "SFLIN", "set6": "LINSS",
    "set7": "SLINS",
}

LOAD_BATCH_QUERY = """
UNWIND $rows AS item
OPTIONAL MATCH (:Report {recordId: item.report.recordId})
      -[:HAS_FIXED_SET]->(:FixedSet)-[legacy:HAS_PERIODIC_SET]->(:PeriodicSet)
WITH item, collect(legacy) AS legacyLinks
FOREACH (legacy IN legacyLinks | DELETE legacy)
MERGE (report:Report {recordId: item.report.recordId})
SET report += item.report
FOREACH (_ IN CASE WHEN item.report.reportType = 'S' THEN [1] ELSE [] END |
    SET report:SmallScaleOperation
)
FOREACH (_ IN CASE WHEN item.report.reportType = 'L' THEN [1] ELSE [] END |
    SET report:LargeScaleOperation
)
FOREACH (_ IN CASE WHEN item.report.reportType = 'E' THEN [1] ELSE [] END |
    SET report:EnemyInitiated
)
FOREACH (_ IN CASE WHEN item.report.reportType = 'W' THEN [1] ELSE [] END |
    SET report:WeeklySummary
)
MERGE (fixed:FixedSet {fixedSetId: item.fixed.fixedSetId})
SET fixed += item.fixed
MERGE (report)-[:HAS_FIXED_SET]->(fixed)
FOREACH (_ IN CASE WHEN item.sourceGroup IS NULL THEN [] ELSE [1] END |
    MERGE (group:SourceGroup {groupKey: item.sourceGroup.groupKey})
    SET group += item.sourceGroup
    MERGE (report)-[:MEMBER_OF]->(group)
)
FOREACH (lookup IN item.lookupCodes |
    FOREACH (_ IN CASE WHEN lookup.kind = 'Nationality' THEN [1] ELSE [] END |
        MERGE (code:Nationality {code: lookup.code})
        SET code.description = lookup.description
        MERGE (report)-[:HAS_NATIONALITY]->(code)
    )
    FOREACH (_ IN CASE WHEN lookup.kind = 'Country' THEN [1] ELSE [] END |
        MERGE (code:Country {code: lookup.code})
        SET code.description = lookup.description
        MERGE (report)-[:HAS_COUNTRY]->(code)
    )
    FOREACH (_ IN CASE WHEN lookup.kind = 'OperationType' THEN [1] ELSE [] END |
        MERGE (code:OperationType {code: lookup.code})
        SET code.description = lookup.description
        MERGE (report)-[:HAS_OPERATION_TYPE]->(code)
    )
    FOREACH (_ IN CASE WHEN lookup.kind = 'Province' THEN [1] ELSE [] END |
        MERGE (code:Province {code: lookup.code})
        SET code.description = lookup.description
        FOREACH (__ IN CASE WHEN lookup.role = 'primary' THEN [1] ELSE [] END |
            MERGE (fixed)-[:HAS_PRIMARY_PROVINCE]->(code)
        )
        FOREACH (__ IN CASE WHEN lookup.role = 'secondary' THEN [1] ELSE [] END |
            MERGE (fixed)-[:HAS_SECONDARY_PROVINCE]->(code)
        )
    )
)
FOREACH (periodic IN item.periodicSets |
    MERGE (periodicSet:PeriodicSet {periodicSetId: periodic.periodicSetId})
    SET periodicSet += periodic.properties
MERGE (report)-[:HAS_PERIODIC_SET]->(periodicSet)
    FOREACH (_ IN CASE WHEN periodic.unit IS NULL THEN [] ELSE [1] END |
        MERGE (unit:Unit {unitKey: periodic.unit.unitKey})
        SET unit += periodic.unit
        MERGE (periodicSet)-[:HAS_UNIT]->(unit)
    )
    FOREACH (_ IN CASE WHEN periodic.aircraftService IS NULL THEN [] ELSE [1] END |
        MERGE (service:AircraftService {serviceKey: periodic.aircraftService})
        SET service.code = periodic.aircraftService
        SET service.description = periodic.aircraftServiceLabel
        MERGE (periodicSet)-[:HAS_AIRCRAFT_SERVICE]->(service)
    )
)
RETURN count(report) AS loaded
"""

INFER_UNIT_LINKS_QUERY = """
MATCH (unit:Unit)<-[:HAS_UNIT]-(:PeriodicSet)<-[:HAS_PERIODIC_SET]-(report:Report)
WHERE $sourceFiles IS NULL OR report.sourceFile IN $sourceFiles
WITH unit, collect(DISTINCT report.recordId) AS recordIds
WHERE size(recordIds) > 1
WITH unit, recordIds,
     reduce(anchor = head(recordIds), recordId IN recordIds |
         CASE WHEN recordId < anchor THEN recordId ELSE anchor END) AS anchorId
UNWIND recordIds AS otherId
WITH unit, anchorId, otherId
WHERE anchorId < otherId
MATCH (a:Report {recordId: anchorId}), (b:Report {recordId: otherId})
WITH a, b, collect(DISTINCT 'shared_unit:' + unit.unitKey) AS evidence
WITH a, b, evidence + CASE
    WHEN a.reportDate IS NOT NULL AND a.reportDate = b.reportDate
    THEN ['shared_date:' + toString(a.reportDate)] ELSE [] END AS evidence
WITH a, b, evidence, 'related:' + a.recordId + '|' + b.recordId AS linkId
MERGE (a)-[link:RELATED_TO {linkId: linkId}]->(b)
ON CREATE SET link.status = 'possible', link.origin = 'metadata_inferred', link.evidence = []
SET link.evidence = reduce(acc = link.evidence, value IN evidence |
    CASE WHEN value IN acc THEN acc ELSE acc + value END)
"""

INFER_PLACE_LINKS_QUERY = """
MATCH (a:Report)
WHERE a.sourceMgrs IS NOT NULL
  AND ($sourceFiles IS NULL OR a.sourceFile IN $sourceFiles)
WITH a.sourceMgrs AS sourceMgrs, collect(DISTINCT a.recordId) AS recordIds
WHERE size(recordIds) > 1
WITH sourceMgrs, recordIds,
     reduce(anchor = head(recordIds), recordId IN recordIds |
         CASE WHEN recordId < anchor THEN recordId ELSE anchor END) AS anchorId
UNWIND recordIds AS otherId
WITH sourceMgrs, anchorId, otherId
WHERE anchorId < otherId
MATCH (a:Report {recordId: anchorId}), (b:Report {recordId: otherId})
WITH a, b, ['shared_place:' + sourceMgrs] AS evidence
WITH a, b, evidence + CASE
    WHEN a.reportDate IS NOT NULL AND a.reportDate = b.reportDate
    THEN ['shared_date:' + toString(a.reportDate)] ELSE [] END AS evidence
WITH a, b, evidence, 'related:' + a.recordId + '|' + b.recordId AS linkId
MERGE (a)-[link:RELATED_TO {linkId: linkId}]->(b)
ON CREATE SET link.status = 'possible', link.origin = 'metadata_inferred', link.evidence = []
SET link.evidence = reduce(acc = link.evidence, value IN evidence |
    CASE WHEN value IN acc THEN acc ELSE acc + value END)
"""


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def parse_date(value: str | None) -> date | None:
    """Convert SITRA YYMMDD or YYDDD values to ISO-ready dates."""
    if not value:
        return None
    raw = value.strip().upper()
    if not raw:
        return None

    julian = raw.endswith("J") or (len(raw) == 5 and raw.isdigit())
    encoded = raw[:-1] if raw.endswith("J") else raw
    try:
        if julian:
            if not re.fullmatch(r"\d{5}", encoded):
                return None
            year_number, day_number = int(encoded[:2]), int(encoded[2:])
            year = _year_from_source(year_number)
            first_day = date(year, 1, 1)
            result = first_day + timedelta(days=day_number - 1)
            return result if result.year == year and day_number > 0 else None
        if re.fullmatch(r"\d{6}", encoded):
            year = _year_from_source(int(encoded[:2]))
            return date(year, int(encoded[2:4]), int(encoded[4:6]))
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", encoded):
            result = date.fromisoformat(encoded)
            return result if 1965 <= result.year <= 1973 else None
    except ValueError:
        return None
    return None


def _year_from_source(two_digit_year: int) -> int:
    if not 65 <= two_digit_year <= 73:
        raise ValueError("date is outside 1965–1973")
    return 1900 + two_digit_year


def _text_fields(fields: dict[str, str]) -> str:
    return normalize_text(" ".join(value for value in fields.values() if value))


def _unit_properties(fields: dict[str, str]) -> dict[str, str] | None:
    identity_fields = ("SVNAT", "COMPY", "BNID", "BRDES", "DVDES")
    identity = [fields.get(name, "") for name in identity_fields]
    if not any(identity[1:]):
        return None
    key = hashlib.sha256(json.dumps(identity, separators=(",", ":")).encode()).hexdigest()
    return {
        "unitKey": key,
        "serviceNationality": identity[0],
        "serviceNationalityLabel": decode_code("SVNAT", identity[0]) if identity[0] else None,
        "company": identity[1],
        "battalionId": identity[2],
        "brigadeDesignation": identity[3],
        "divisionDesignation": identity[4],
    }


def parse_record(line: str, source_file: Path, line_number: int) -> dict[str, Any] | None:
    if len(line) != RECORD_WIDTH:
        return None
    fields = {name: normalize_text(line[start:end]) for name, (start, end, _) in FIELDS.items()}
    record_id = f"{quote(source_file.name, safe='._-')}:{line_number}"
    report = {
        "recordId": record_id,
        "sourceFile": source_file.name,
        "sourceRecordNumber": line_number,
        "reportType": fields["DATAT"],
        "serial": fields["SERAL"],
        "paragraphNumber": fields["SERAL"],
        "militaryRegion": fields["CORP"],
        "part": fields["PART"],
        "reportDateRaw": fields["DATE"],
        "searchText": _text_fields(fields),
    }
    report.update(code_label_fields({name: fields[name] for name in ("DATAT", "CORP", "PART")}, fields["DATAT"]))
    for name, (_, _, group) in FIELDS.items():
        if group == "control" and name != "DATE" and fields[name]:
            report[name.lower()] = fields[name]
    report_date = parse_date(fields["DATE"])
    if report_date:
        report["reportDate"] = report_date

    raw_utm = fields["UTM"]
    report["sourceUtm"] = raw_utm
    coordinate = convert_to_latlong(raw_utm)
    if coordinate:
        report.update({
            "mgrsGzd": coordinate.gzd,
            "sourceMgrs": coordinate.mgrs,
            "latitude": coordinate.latitude,
            "longitude": coordinate.longitude,
        })

    fixed = {
        "fixedSetId": f"{record_id}:fixed",
        "sourceFile": source_file.name,
        "operationName": fields["OPNAM"],
        "operationCode": fields["OPCOD"],
        "updateDateRaw": fields["UDATE"],
    }
    for name, (_, _, group) in FIELDS.items():
        if group == "fixed" and name != "UDATE" and fields[name]:
            fixed[name.lower()] = fields[name]
    fixed.update(code_label_fields({name: fields[name] for name in ("FNATL", "CNTRY", "OPCOD", "PRVC1", "PRVC2", "PRVC3")}, fields["DATAT"]))
    update_date = parse_date(fields["UDATE"])
    if update_date:
        fixed["updateDate"] = update_date
    if fields["DTEI"]:
        initiation = parse_date(fields["DTEI"])
        if initiation:
            report["initiationDate"] = initiation
        report["initiationDateRaw"] = fields["DTEI"]
    if fields["DTET"]:
        termination = parse_date(fields["DTET"])
        if termination:
            report["terminationDate"] = termination
        report["terminationDateRaw"] = fields["DTET"]
    if fields["HOURI"]:
        report["initiationHour"] = fields["HOURI"]
    if fields["HOURT"]:
        report["terminationHour"] = fields["HOURT"]

    source_group = None
    controls = [fields[name] for name in ("DATE", "DATAT", "SERAL", "CORP", "PART")]
    if all(controls) and report_date:
        group_key = hashlib.sha256(json.dumps(controls, separators=(",", ":")).encode()).hexdigest()
        source_group = {
            "groupKey": group_key,
            "messageSentDate": report_date,
            "reportType": fields["DATAT"],
            "reportTypeLabel": decode_code("DATAT", fields["DATAT"]) if fields["DATAT"] else None,
            "paragraphNumber": fields["SERAL"],
            "militaryRegion": fields["CORP"],
            "part": fields["PART"],
            "sourceControlValues": "|".join(controls),
        }

    lookup_codes = []
    for kind, name in (("Nationality", "FNATL"), ("Country", "CNTRY"), ("OperationType", "OPCOD")):
        if fields[name]:
            lookup_codes.append({"kind": kind, "code": fields[name], "description": decode_code(name, fields[name], fields["DATAT"])})
    for role, name in (("primary", "PRVC1"), ("secondary", "PRVC2"), ("secondary", "PRVC3")):
        if fields[name]:
            lookup_codes.append({"kind": "Province", "role": role, "code": fields[name], "description": decode_code(name, fields[name], fields["DATAT"])})

    periodic_sets = []
    for set_name, kind in SET_KINDS.items():
        set_fields = {name: fields[name] for name, (_, _, group) in FIELDS.items() if group == set_name}
        if not any(set_fields.values()):
            continue
        line_field = SET_LINE_FIELDS[set_name]
        props: dict[str, Any] = {
            "periodicSetId": f"{record_id}:{set_name}",
            "sourceFile": source_file.name,
            "sourceRecordNumber": line_number,
            "kind": kind,
            "lineNumber": set_fields.get(line_field, ""),
            "searchText": _text_fields(set_fields),
        }
        props.update({name.lower(): value for name, value in set_fields.items() if value})
        props.update(code_label_fields(set_fields, fields["DATAT"]))
        unit = _unit_properties(set_fields) if set_name == "set3" else None
        periodic_sets.append({
            "periodicSetId": props.pop("periodicSetId"),
            "properties": props,
            "unit": unit,
            "aircraftService": fields["ARSVC"] if set_name == "set1" and fields["ARSVC"] else None,
            "aircraftServiceLabel": props.get("arsvcLabel"),
        })

    decoded_labels = code_label_fields(fields, fields["DATAT"])
    report["searchText"] = normalize_text(" ".join([report["searchText"], *decoded_labels.values()]))
    for periodic in periodic_sets:
        periodic["properties"]["searchText"] = normalize_text(
            " ".join([periodic["properties"]["searchText"], *(
                value for key, value in periodic["properties"].items() if key.endswith("Label")
            )])
        )

    return {
        "report": report,
        "fixed": fixed,
        "sourceGroup": source_group,
        "lookupCodes": lookup_codes,
        "periodicSets": periodic_sets,
    }


def read_records(source: Path) -> tuple[Iterable[dict[str, Any]], dict[str, int]]:
    counts = {"read": 0, "skipped": 0, "withoutDate": 0, "withoutCoordinates": 0}

    def records() -> Iterable[dict[str, Any]]:
        with source.open("rb") as stream:
            for line_number, raw_line in enumerate(stream, 1):
                line = raw_line.rstrip(b"\r\n")
                if not line:
                    counts["skipped"] += 1
                    continue
                counts["read"] += 1
                if len(line) != RECORD_WIDTH:
                    counts["skipped"] += 1
                    continue
                try:
                    text = line.decode("ascii")
                except UnicodeDecodeError:
                    counts["skipped"] += 1
                    continue
                record = parse_record(text, source, line_number)
                if record is None:
                    counts["skipped"] += 1
                    continue
                if "reportDate" not in record["report"]:
                    counts["withoutDate"] += 1
                if "latitude" not in record["report"]:
                    counts["withoutCoordinates"] += 1
                yield record

    return records(), counts


def _load_batch(tx: Any, rows: list[dict[str, Any]]) -> int:
    result = tx.run(LOAD_BATCH_QUERY, rows=rows)
    record = result.single()
    return record["loaded"] if record else 0


def load_source(driver: Driver, source: Path, database: str = "neo4j", batch_size: int = BATCH_SIZE) -> dict[str, int]:
    records, counts = read_records(source)
    loaded = 0
    batch = []
    with driver.session(database=database) as session:
        for record in records:
            batch.append(record)
            if len(batch) >= batch_size:
                loaded += session.execute_write(_load_batch, batch)
                batch = []
        if batch:
            loaded += session.execute_write(_load_batch, batch)
    counts["loaded"] = loaded
    return counts


def infer_possible_links(
    driver: Driver, database: str = "neo4j", source_files: list[str] | None = None
) -> None:
    with driver.session(database=database) as session:
        session.run(INFER_UNIT_LINKS_QUERY, sourceFiles=source_files).consume()
        session.run(INFER_PLACE_LINKS_QUERY, sourceFiles=source_files).consume()


def main() -> None:
    parser = argparse.ArgumentParser(description="Import the NARA SITRA ASCII translation into Neo4j.")
    parser.add_argument("--source", type=Path, action="append", required=True, help="SITRA translated text file; repeat for additional year files")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    args = parser.parse_args()
    missing = [source for source in args.source if not source.is_file()]
    if missing:
        parser.error("source file not found: " + ", ".join(str(path) for path in missing))
    if args.batch_size < 1:
        parser.error("batch size must be greater than zero")

    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    total = {"loaded": 0, "skipped": 0, "withoutDate": 0, "withoutCoordinates": 0}
    with GraphDatabase.driver(uri) as driver:
        driver.verify_connectivity()
        apply_schema(driver, database)
        for source in args.source:
            result = load_source(driver, source, database, args.batch_size)
            print(f"{source.name}: {result}")
            for name in total:
                total[name] += result[name]
        infer_possible_links(driver, database)
    print(f"Total: {total}")


if __name__ == "__main__":
    main()
