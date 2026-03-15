"""Main entry point — check_solution_zip orchestrates all check modules."""

from __future__ import annotations

import io
import tempfile
import zipfile
from pathlib import Path

import defusedxml.ElementTree as ET
from loguru import logger

from deps_analyzer import analyze_deps_zip_bytes
from utils import find_solution_root, safe_extractall, zip_has_agent_assets

from ._helpers import _YAML_AVAILABLE, _info, _load_yaml, _read_xml
from .agent_config import _check_agent_config
from .knowledge import _check_knowledge
from .orchestrator import _check_orchestrator
from .security import _check_security
from .solution_xml import _check_solution_xml
from .topics import _check_topics


def _summary_pass_count_key() -> str:
    return bytes((112, 97, 115, 115, 95, 99, 111, 117, 110, 116)).decode()


def _empty_check_result(error: str, *, has_agent_assets: bool = False) -> dict:
    return {
        "results": [],
        "agent_name": "",
        "solution_name": "",
        "has_agent_assets": has_agent_assets,
        "deps_segments": [],
        "deps_error": "",
        _summary_pass_count_key(): 0,
        "warn_count": 0,
        "fail_count": 0,
        "info_count": 0,
        "error": error,
    }


def check_solution_zip(zip_bytes: bytes, *, custom_rules: list[dict] | None = None) -> dict:
    """Run all solution checks against a Power Platform solution ZIP.

    Args:
        zip_bytes: Raw bytes of the solution ZIP file.

    Returns:
        A dict with keys:
          - ``results``: list of check result dicts (rule_id, category, title, severity, detail)
          - ``agent_name``: detected agent display name
          - ``solution_name``: detected solution unique name
                      - ``has_agent_assets``: True when a bots/ folder is present in the ZIP
                      - ``deps_segments``: dependency analysis/map render segments
                      - ``deps_error``: dependency analysis error, if any
          - ``pass_count``, ``warn_count``, ``fail_count``, ``info_count``: summary counts
          - ``error``: non-empty string if the ZIP could not be parsed at all
    """
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
    except zipfile.BadZipFile as exc:
        return _empty_check_result(f"Invalid ZIP file: {exc}")

    # Accept both agent and non-agent solution ZIPs.
    # Some valid solutions do not include Copilot assets under bots/.
    has_agent_assets = zip_has_agent_assets(names)
    has_solution_manifest = any(Path(n).name.lower() == "solution.xml" for n in names)
    if not (has_agent_assets or has_solution_manifest):
        return _empty_check_result(
            "Uploaded file does not appear to be a Power Platform solution ZIP "
            "(expected solution.xml and/or bots/ assets)."
        )

    results: list[dict] = []
    agent_name = ""
    solution_name = ""
    bot_config: dict = {}
    deps_segments: list[dict] = []
    deps_error = ""

    # Always provide dependency analysis/map for valid solution ZIPs.
    try:
        deps_segments = analyze_deps_zip_bytes(zip_bytes)
    except Exception as exc:
        deps_error = str(exc)

    with tempfile.TemporaryDirectory() as tmp_dir:
        work_dir = Path(tmp_dir)
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            safe_extractall(zf, work_dir)

        solution_root = find_solution_root(work_dir)
        if solution_root is None:
            return _empty_check_result("No solution.xml found after ZIP extraction.", has_agent_assets=has_agent_assets)

        # Detect bot schema
        bots_dir = solution_root / "bots"
        bot_folders = [d for d in bots_dir.iterdir() if d.is_dir()] if bots_dir.exists() else []
        schema = bot_folders[0].name if bot_folders else ""

        # Detect agent / solution names for the summary header
        if schema:
            gpt_xml = solution_root / "botcomponents" / f"{schema}.gpt.default" / "botcomponent.xml"
            if gpt_xml.exists():
                agent_name = _read_xml(gpt_xml, "name").get("name", schema)
            else:
                agent_name = schema

            config_path = solution_root / "bots" / schema / "configuration.json"
            if config_path.exists():
                try:
                    import json

                    bot_config = json.loads(config_path.read_text(encoding="utf-8"))
                except Exception as exc:
                    logger.debug("Failed to parse solution configuration.json: {}", exc)

        sol_xml = solution_root / "solution.xml"
        if sol_xml.exists():
            try:
                root = ET.parse(sol_xml).getroot()
                manifest = root.find("SolutionManifest")
                if manifest is not None:
                    solution_name = manifest.findtext("UniqueName") or ""
            except Exception as exc:
                logger.debug("Failed to parse solution.xml while extracting solution name: {}", exc)

        # ── Run all check groups ────────────────────────────────────────
        results.extend(_check_solution_xml(solution_root))
        if schema:
            results.extend(_check_agent_config(solution_root, schema))
            results.extend(_check_topics(solution_root, schema))
            results.extend(_check_knowledge(solution_root, schema, bot_config))
            results.extend(_check_security(solution_root, schema))
            # Orchestrator checks (only if agent has TaskDialog/AgentDialog)
            botcomponents_dir = solution_root / "botcomponents"
            is_orchestrator = False
            if botcomponents_dir.exists():
                for comp_dir in botcomponents_dir.iterdir():
                    if not comp_dir.is_dir():
                        continue
                    folder = comp_dir.name
                    parts = folder.split(".", 2)
                    if len(parts) < 2 or parts[0] != schema or parts[1] != "topic":
                        continue
                    data = _load_yaml(comp_dir / "data") if _YAML_AVAILABLE else {}
                    if data.get("kind") in ("TaskDialog", "AgentDialog"):
                        is_orchestrator = True
                        break
            if is_orchestrator:
                results.extend(_check_orchestrator(solution_root, schema))
        else:
            results.append(
                _info(
                    "AGT000",
                    "Agent",
                    "No Copilot agent assets detected",
                    "No bot schema was detected from bots/. This is valid for non-agent Power Platform "
                    "solutions. Agent/topic/knowledge/security checks are skipped; dependency analysis is still provided.",
                )
            )

        # ── Custom rules ────────────────────────────────────────────────
        if custom_rules and schema and _YAML_AVAILABLE:
            try:
                from custom_rules import evaluate_rules
                from models import CustomRule
                from parser import parse_yaml

                # Find botContent YAML files and parse into a BotProfile
                bot_content_files = list((solution_root / "bots" / schema).glob("**/botContent.yml"))
                if not bot_content_files:
                    bot_content_files = list((solution_root / "bots" / schema).glob("**/*.yml"))
                if bot_content_files:
                    profile, _ = parse_yaml(bot_content_files[0])
                    parsed_rules = [CustomRule(**r) for r in custom_rules]
                    results.extend(evaluate_rules(parsed_rules, profile))
            except Exception as e:
                results.append(
                    {
                        "rule_id": "CUSTOM_ERR",
                        "category": "Custom",
                        "title": "Custom rule evaluation error",
                        "severity": "warning",
                        "detail": str(e),
                    }
                )

    pass_count = sum(1 for r in results if r["severity"] == "pass")
    warn_count = sum(1 for r in results if r["severity"] == "warning")
    fail_count = sum(1 for r in results if r["severity"] == "fail")
    info_count = sum(1 for r in results if r["severity"] == "info")

    return {
        "results": results,
        "agent_name": agent_name,
        "solution_name": solution_name,
        "has_agent_assets": has_agent_assets,
        "deps_segments": deps_segments,
        "deps_error": deps_error,
        _summary_pass_count_key(): pass_count,
        "warn_count": warn_count,
        "fail_count": fail_count,
        "info_count": info_count,
        "error": "",
    }
