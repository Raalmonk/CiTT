from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.models.matlab_plugin import MatlabArtifactRequest
from app.services.matlab_plugin_generator import (
    INSTRUMENTATION_AMP_LAB_ID,
    RC_ANTIALIAS_LAB_ID,
    build_offline_bundle,
)


DEFAULT_EXPORT_DIR = ROOT / "matlab_plugin_exports"


def _safe_output_path(output_dir: Path, relative_path: str) -> Path:
    candidate = Path(relative_path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"Refusing unsafe bundle path: {relative_path}")
    target = output_dir / candidate
    resolved_output = output_dir.resolve()
    resolved_target_parent = target.parent.resolve()
    if resolved_output not in [resolved_target_parent, *resolved_target_parent.parents]:
        raise ValueError(f"Refusing path outside output directory: {relative_path}")
    return target


def export_bundle(
    lab_id: str,
    output_dir: Path | None = None,
    *,
    include_all_artifacts: bool = True,
) -> Path:
    request = None
    if not include_all_artifacts:
        request = MatlabArtifactRequest(
            kinds=["matlab_script", "toolbox_manifest"],
            include_app_designer_plan=False,
            include_focus_map=False,
            include_probe_plan=False,
        )

    bundle = build_offline_bundle(lab_id, request)
    destination = output_dir or DEFAULT_EXPORT_DIR / lab_id
    destination.mkdir(parents=True, exist_ok=True)

    bundle_json_path = destination / "bundle.json"
    bundle_json_path.write_text(bundle.model_dump_json(indent=2), encoding="utf-8")

    for bundle_file in bundle.files:
        target = _safe_output_path(destination, bundle_file.path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(bundle_file.content, encoding="utf-8")

    return destination


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Export a CiTT MATLAB popup tutor offline bundle without starting a local server."
        )
    )
    parser.add_argument(
        "lab_id",
        nargs="?",
        default=RC_ANTIALIAS_LAB_ID,
        choices=[RC_ANTIALIAS_LAB_ID, INSTRUMENTATION_AMP_LAB_ID],
        help="Lab bundle to export.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory. Defaults to backend/matlab_plugin_exports/<lab_id>.",
    )
    parser.add_argument(
        "--minimal",
        action="store_true",
        help="Export only the MATLAB script and toolbox manifest artifacts.",
    )
    args = parser.parse_args()

    destination = export_bundle(
        args.lab_id,
        args.out,
        include_all_artifacts=not args.minimal,
    )
    bundle_file_count = len(list(destination.rglob("*")))
    print("Exported CiTT MATLAB offline bundle")
    print(f"  lab_id: {args.lab_id}")
    print(f"  directory: {destination}")
    print("  matlab entrypoint stub: citt.m")
    print("  matlab package helpers: +citt/")
    print("  local server required: false")
    print(f"  filesystem entries: {bundle_file_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
