"""Export the deterministic FastAPI OpenAPI contract for frontend code generation."""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api.application import create_app  # noqa: E402
from core.config import Settings  # noqa: E402


def export_openapi(output_path: Path) -> None:
    app = create_app(Settings(_env_file=None))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    export_openapi(arguments.output.resolve())


if __name__ == "__main__":
    main()
