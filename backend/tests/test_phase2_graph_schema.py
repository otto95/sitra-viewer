import sys
from unittest.mock import MagicMock, patch

import pytest
from neo4j import GraphDatabase

from app import graph_schema


def test_schema_statements_cover_identity_search_and_dates() -> None:
    statements = graph_schema.schema_statements()
    joined = "\n".join(statements)

    assert "report_record_id" in joined
    assert "related_link_id" in joined
    assert "report_message_sent_date" in joined
    assert "report_search" in joined


def test_related_link_id_is_order_independent() -> None:
    forward = graph_schema.related_link_id("record-a", "record-b")
    reverse = graph_schema.related_link_id("record-b", "record-a")

    assert forward == reverse
    assert forward != graph_schema.related_link_id("record-a", "record-c")


def test_related_link_id_rejects_a_self_link() -> None:
    with pytest.raises(ValueError, match="cannot be linked to itself"):
        graph_schema.related_link_id("record-a", "record-a")


@pytest.mark.parametrize("command", ["setup", "validate-sample", "cleanup-sample"])
def test_graph_schema_cli_dispatches_command(command: str, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_driver = MagicMock()
    fake_driver.__enter__.return_value = fake_driver
    monkeypatch.setenv("NEO4J_URI", "bolt://example:7687")
    monkeypatch.setenv("NEO4J_DATABASE", "sitra")
    monkeypatch.setattr(sys, "argv", ["graph_schema", command])

    with (
        patch.object(GraphDatabase, "driver", return_value=fake_driver) as driver_factory,
        patch.object(graph_schema, "apply_schema") as apply_schema,
        patch.object(graph_schema, "validate_sample_graph", return_value={}) as validate_sample,
        patch.object(graph_schema, "cleanup_sample_graph") as cleanup_sample,
    ):
        graph_schema.main()

    driver_factory.assert_called_once_with("bolt://example:7687")
    fake_driver.verify_connectivity.assert_called_once_with()
    if command == "setup":
        apply_schema.assert_called_once_with(fake_driver, "sitra")
    elif command == "validate-sample":
        apply_schema.assert_called_once_with(fake_driver, "sitra")
        validate_sample.assert_called_once_with(fake_driver, "sitra")
    else:
        cleanup_sample.assert_called_once_with(fake_driver, "sitra")


def test_import_command_requires_an_existing_source(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "missing.dat"
    monkeypatch.setattr(sys, "argv", ["import_data", "--source", str(source)])

    with pytest.raises(SystemExit) as exit_info:
        from app.import_data import main

        main()

    assert exit_info.value.code == 2
    assert "source file not found" in capsys.readouterr().err


def test_import_command_loads_explicit_sources_separately_from_startup(
    monkeypatch: pytest.MonkeyPatch, tmp_path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "sitra.dat"
    source.write_text("demo source")
    monkeypatch.setattr(sys, "argv", ["import_data", "--source", str(source)])
    from app import import_data

    fake_driver = MagicMock()
    fake_driver.__enter__.return_value = fake_driver
    counts = {"loaded": 1, "skipped": 0, "withoutDate": 0, "withoutCoordinates": 1}
    with (
        patch.object(import_data.GraphDatabase, "driver", return_value=fake_driver),
        patch.object(import_data, "apply_schema") as apply_schema,
        patch.object(import_data, "load_source", return_value=counts) as load_source,
        patch.object(import_data, "infer_possible_links") as infer_links,
    ):
        import_data.main()

    apply_schema.assert_called_once_with(fake_driver, "neo4j")
    load_source.assert_called_once_with(fake_driver, source, "neo4j", 1000)
    infer_links.assert_called_once_with(fake_driver, "neo4j")
    assert "loaded': 1" in capsys.readouterr().out


def test_health_endpoint_function() -> None:
    from app.main import health

    assert health() == {"status": "ok"}


def test_neo4j_integration_schema_and_link_promotion() -> None:
    uri = graph_schema.os.getenv("NEO4J_URI", "bolt://localhost:7687")
    database = graph_schema.os.getenv("NEO4J_DATABASE", "neo4j")

    with GraphDatabase.driver(uri) as driver:
        driver.verify_connectivity()
        graph_schema.apply_schema(driver, database)
        result = graph_schema.validate_sample_graph(driver, database)

    assert result["recordsInDateRange"] == 3
    assert result["promotedStatus"] == "definite"
    assert result["evidenceRetained"] is True
    assert result["sourceControlGroup"]["part"] == "A"
