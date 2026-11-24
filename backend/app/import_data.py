import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import a local SITRA source file into Neo4j."
    )
    parser.add_argument("--source", type=Path, required=True, help="Path under /data")
    args = parser.parse_args()

    if not args.source.is_file():
        parser.error(f"source file not found: {args.source}")

    parser.exit(
        2,
        "The import entry point is scaffolded; data loading is implemented in Phase 3.\n",
    )


if __name__ == "__main__":
    main()
