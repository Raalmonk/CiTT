from __future__ import annotations

import importlib.util
from pathlib import Path

from app.services.matlab_plugin_generator import RC_ANTIALIAS_LAB_ID


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "export_matlab_offline_bundle.py"
SPEC = importlib.util.spec_from_file_location("export_matlab_offline_bundle", SCRIPT_PATH)
export_module = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(export_module)


def test_export_matlab_offline_bundle_writes_entrypoint_and_json(tmp_path):
    destination = export_module.export_bundle(RC_ANTIALIAS_LAB_ID, tmp_path)

    assert destination == tmp_path
    assert (tmp_path / "bundle.json").exists()
    assert (tmp_path / "citt.m").exists()
    assert (tmp_path / "+citt" / "citt.m").exists()
    assert (tmp_path / "+citt" / "loadOfflineBundle.m").exists()
    assert (tmp_path / "+citt" / "openPopup.m").exists()
    assert (tmp_path / "examples" / RC_ANTIALIAS_LAB_ID / "manifest.json").exists()
    assert (tmp_path / "examples" / RC_ANTIALIAS_LAB_ID / "lab_plan.json").exists()
    assert (tmp_path / "docs" / "offline_first.md").exists()

    entrypoint = (tmp_path / "citt.m").read_text(encoding="utf-8")
    popup = (tmp_path / "+citt" / "openPopup.m").read_text(encoding="utf-8")
    assert "function varargout = citt" in entrypoint
    assert "citt.openPopup" in entrypoint
    assert "uifigure" in popup
    assert "uitabgroup" in popup


def test_export_matlab_offline_bundle_refuses_path_traversal(tmp_path):
    try:
        export_module._safe_output_path(tmp_path, "../outside.m")
    except ValueError as exc:
        assert "unsafe bundle path" in str(exc)
    else:
        raise AssertionError("Expected unsafe path to be rejected.")
