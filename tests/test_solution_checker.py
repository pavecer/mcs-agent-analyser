from __future__ import annotations

import io
import tempfile
import zipfile
from pathlib import Path

from deps_analyzer import analyze_deps_zip_bytes, analyze_deps_zip_bytes_report
from solution_checker import check_solution_zip
from utils import is_zip_filename, safe_extractall, safe_temp_path
from validator import validate_instructions, validate_zip_bytes


def _zip_bytes(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, content in files.items():
            zf.writestr(path, content)
    return buf.getvalue()


def test_solution_checker_accepts_non_agent_solution_and_returns_dependency_map():
    zip_bytes = _zip_bytes(
        {
            "solution.xml": """
<ImportExportXml>
  <SolutionManifest>
    <UniqueName>NonAgentSolution</UniqueName>
    <Version>1.2.3.4</Version>
    <Managed>0</Managed>
    <Publisher>
      <UniqueName>contoso</UniqueName>
      <CustomizationPrefix>cts</CustomizationPrefix>
    </Publisher>
    <Descriptions>
      <Description description="Generic non-agent solution" />
    </Descriptions>
    <RootComponents>
      <RootComponent type="44" id="{11111111-2222-3333-4444-555555555555}" schemaName="cts_env_var" />
    </RootComponents>
  </SolutionManifest>
</ImportExportXml>
""".strip(),
        }
    )

    result = check_solution_zip(zip_bytes)

    assert result["error"] == ""
    assert result["solution_name"] == "NonAgentSolution"
    assert result["has_agent_assets"] is False

    # Non-agent ZIPs are accepted; agent checks are skipped with informational severity.
    agt000 = [r for r in result["results"] if r["rule_id"] == "AGT000"]
    assert agt000
    assert agt000[0]["severity"] == "info"

    # Dependency analysis/map is included in checker payload.
    assert isinstance(result["deps_segments"], list)
    assert len(result["deps_segments"]) == 2
    assert result["deps_segments"][0]["type"] == "text"
    assert result["deps_segments"][1]["type"] == "mermaid"


def test_solution_checker_rejects_non_solution_zip():
    zip_bytes = _zip_bytes({"README.txt": "hello"})

    result = check_solution_zip(zip_bytes)

    assert result["results"] == []
    assert result["error"] != ""
    assert "solution" in result["error"].lower()
    assert result["deps_segments"] == []


def test_deps_report_returns_component_and_relation_rows_with_dedup():
    zip_bytes = _zip_bytes(
        {
            "solution.xml": """
<ImportExportXml>
  <SolutionManifest>
    <UniqueName>DepsRichSolution</UniqueName>
    <Version>1.0.0.0</Version>
    <Managed>0</Managed>
    <Publisher>
      <UniqueName>contoso</UniqueName>
      <CustomizationPrefix>cts</CustomizationPrefix>
    </Publisher>
    <Descriptions>
      <Description description="Deps test solution" />
    </Descriptions>
    <RootComponents>
      <RootComponent type="44" id="{aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb}" schemaName="cts_env" />
      <RootComponent type="430" id="{cccccccc-1111-2222-3333-dddddddddddd}" schemaName="cts_agent" />
    </RootComponents>
    <MissingDependencies>
      <MissingDependency>
        <Required type="10066" displayName="Conn Ref A" schemaName="cts_conn_ref_a" />
        <Dependent id="{cccccccc-1111-2222-3333-dddddddddddd}" />
      </MissingDependency>
      <MissingDependency>
        <Required type="10066" displayName="Conn Ref A" schemaName="cts_conn_ref_a" />
        <Dependent id="{cccccccc-1111-2222-3333-dddddddddddd}" />
      </MissingDependency>
      <MissingDependency>
        <Required type="44" displayName="Env Var B" schemaName="cts_env_b" />
        <Dependent id="{aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb}" />
      </MissingDependency>
    </MissingDependencies>
  </SolutionManifest>
</ImportExportXml>
""".strip(),
        }
    )

    report = analyze_deps_zip_bytes_report(zip_bytes, detailed_diagram=True)

    assert report["summary_markdown"]
    assert report["mermaid"]

    component_rows = report["component_rows"]
    assert isinstance(component_rows, list)
    assert len(component_rows) == 2
    assert {row["schema"] for row in component_rows} == {"cts_env", "cts_agent"}

    relation_rows = report["relation_rows"]
    assert isinstance(relation_rows, list)
    # duplicate missing dependency should be collapsed to one row
    assert len(relation_rows) == 2
    required_names = {row["required"] for row in relation_rows}
    assert required_names == {"Conn Ref A", "Env Var B"}
    assert all(row["source"] == "solution.xml" for row in relation_rows)


def test_deps_segments_api_remains_backward_compatible():
    zip_bytes = _zip_bytes(
        {
            "solution.xml": """
<ImportExportXml>
  <SolutionManifest>
    <UniqueName>CompatSolution</UniqueName>
    <Version>1.0.0.0</Version>
    <Managed>0</Managed>
    <Publisher>
      <UniqueName>contoso</UniqueName>
      <CustomizationPrefix>cts</CustomizationPrefix>
    </Publisher>
    <Descriptions>
      <Description description="Compat test solution" />
    </Descriptions>
    <RootComponents>
      <RootComponent type="44" id="{11111111-2222-3333-4444-555555555555}" schemaName="cts_env_var" />
    </RootComponents>
  </SolutionManifest>
</ImportExportXml>
""".strip(),
        }
    )

    segments = analyze_deps_zip_bytes(zip_bytes)

    assert isinstance(segments, list)
    assert len(segments) == 2
    assert segments[0]["type"] == "text"
    assert segments[1]["type"] == "mermaid"
    assert segments[0]["content"]
    assert segments[1]["content"]


def test_deps_mermaid_escapes_problematic_missing_dependency_names():
    zip_bytes = _zip_bytes(
        {
            "solution.xml": """
<ImportExportXml>
  <SolutionManifest>
    <UniqueName>EscapingSolution</UniqueName>
    <Version>1.0.0.0</Version>
    <Managed>0</Managed>
    <Publisher>
      <UniqueName>contoso</UniqueName>
      <CustomizationPrefix>cts</CustomizationPrefix>
    </Publisher>
    <Descriptions>
      <Description description="Escaping test" />
    </Descriptions>
    <RootComponents>
      <RootComponent type="430" id="{aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb}" schemaName="cts_agent" />
    </RootComponents>
    <MissingDependencies>
      <MissingDependency>
        <Required type="401" displayName="[ESSPRMPT] ServiceNow Items AC&quot;" schemaName="svc_now_items" />
        <Dependent id="{aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb}" />
      </MissingDependency>
    </MissingDependencies>
  </SolutionManifest>
</ImportExportXml>
""".strip(),
        }
    )

    report = analyze_deps_zip_bytes_report(zip_bytes, detailed_diagram=True)
    mermaid = report["mermaid"]

    assert "flowchart TD" in mermaid
    assert "MDEP0" in mermaid
    assert "\"\"]" not in mermaid
    assert "[ESSPRMPT]" not in mermaid


def test_safe_extractall_rejects_path_traversal_entries():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("../escape.txt", "blocked")

    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(io.BytesIO(buf.getvalue())) as zf:
            try:
                safe_extractall(zf, Path(tmpdir))
            except ValueError as exc:
                assert "unsafe ZIP entry" in str(exc)
            else:
                raise AssertionError("Expected unsafe ZIP entry to be rejected")


def test_safe_temp_path_strips_directory_components():
    path = safe_temp_path("/tmp/work", "../../nested/botContent.yml", "fallback.yml")
    assert path == Path("/tmp/work") / "botContent.yml"


def test_safe_temp_path_uses_default_for_empty_filename():
    path = safe_temp_path("/tmp/work", "", "fallback.zip")
    assert path == Path("/tmp/work") / "fallback.zip"


def test_is_zip_filename_accepts_zip_only():
  assert is_zip_filename("solution.zip") is True
  assert is_zip_filename("solution.ZIP") is True
  assert is_zip_filename("solution.json") is False
  assert is_zip_filename(None) is False


def test_solution_checker_detects_agent_assets_in_nested_export_root():
    zip_bytes = _zip_bytes(
        {
            "ExportRoot/solution.xml": """
<ImportExportXml>
  <SolutionManifest>
    <UniqueName>NestedAgentSolution</UniqueName>
    <Version>1.0.0.0</Version>
    <Managed>0</Managed>
    <Publisher>
      <UniqueName>contoso</UniqueName>
      <CustomizationPrefix>cts</CustomizationPrefix>
    </Publisher>
    <Descriptions>
      <Description description="Nested root test" />
    </Descriptions>
  </SolutionManifest>
</ImportExportXml>
""".strip(),
            "ExportRoot/bots/sample_agent/bot.xml": "<bot><name>Sample Agent</name></bot>",
            "ExportRoot/botcomponents/sample_agent.gpt.default/botcomponent.xml": "<botcomponent><name>Sample Agent</name></botcomponent>",
            "ExportRoot/botcomponents/sample_agent.gpt.default/data": "instructions: test\n",
            "ExportRoot/bots/sample_agent/configuration.json": "{}",
        }
    )

    result = check_solution_zip(zip_bytes)

    assert result["error"] == ""
    assert result["has_agent_assets"] is True
    assert result["solution_name"] == "NestedAgentSolution"


def test_solution_checker_accepts_non_agent_nested_export_root():
    zip_bytes = _zip_bytes(
        {
            "NonAgentRoot/solution.xml": """
<ImportExportXml>
  <SolutionManifest>
    <UniqueName>NestedNonAgentSolution</UniqueName>
    <Version>1.0.0.0</Version>
    <Managed>0</Managed>
    <Publisher>
      <UniqueName>contoso</UniqueName>
      <CustomizationPrefix>cts</CustomizationPrefix>
    </Publisher>
    <Descriptions>
      <Description description="Nested root non-agent test" />
    </Descriptions>
  </SolutionManifest>
</ImportExportXml>
""".strip(),
        }
    )

    result = check_solution_zip(zip_bytes)

    assert result["error"] == ""
    assert result["has_agent_assets"] is False
    assert result["solution_name"] == "NestedNonAgentSolution"


def test_deps_report_allows_solution_without_root_components():
    zip_bytes = _zip_bytes(
        {
            "NoComponents/solution.xml": """
<ImportExportXml>
  <SolutionManifest>
    <UniqueName>NoComponentsSolution</UniqueName>
    <Version>1.0.0.0</Version>
    <Managed>0</Managed>
    <Publisher>
      <UniqueName>contoso</UniqueName>
      <CustomizationPrefix>cts</CustomizationPrefix>
    </Publisher>
    <Descriptions>
      <Description description="No root components" />
    </Descriptions>
  </SolutionManifest>
</ImportExportXml>
""".strip(),
        }
    )

    report = analyze_deps_zip_bytes_report(zip_bytes)

    assert ("NoComponentsSolution" in report["summary_markdown"]) or (
      "No root components" in report["summary_markdown"]
    )
    assert isinstance(report["component_rows"], list)
    assert report["component_rows"] == []


def test_validate_zip_resolves_model_hint_from_ai_settings():
    zip_bytes = _zip_bytes(
        {
            "solution.xml": """
<ImportExportXml>
  <SolutionManifest>
    <UniqueName>ValidatorHintSolution</UniqueName>
    <Version>1.0.0.0</Version>
    <Managed>0</Managed>
    <Publisher>
      <UniqueName>contoso</UniqueName>
      <CustomizationPrefix>cts</CustomizationPrefix>
    </Publisher>
    <Descriptions>
      <Description description="Validator hint test" />
    </Descriptions>
  </SolutionManifest>
</ImportExportXml>
""".strip(),
            "bots/sample_agent/configuration.json": "{}",
            "botcomponents/sample_agent.gpt.default/data": """
kind: GptComponentMetadata
displayName: Sample Agent
instructions: |
  You are a helpful assistant.
aISettings:
  model:
    modelNameHint: GPT5Chat
""".strip(),
        }
    )

    result = validate_zip_bytes(zip_bytes)

    assert result["model_key"] == "gpt5chat"
    assert result["model_display"] == "GPT-5 Chat"
    assert result["best_practices_md"]


def test_validate_instructions_legacy_model_profiles_are_assessed():
    r_4o = validate_instructions("You are a helpful assistant.", "GPT4o")
    r_4o_mini = validate_instructions("You are a helpful assistant.", "gpt-4o-mini")
    r_4 = validate_instructions("You are a helpful assistant.", "gpt-4")

    assert r_4o["model_key"] == "gpt4o"
    assert r_4o["model_display"] == "GPT-4o"
    assert r_4o["best_practices_md"]
    assert r_4o["results"]

    assert r_4o_mini["model_key"] == "gpt4omini"
    assert r_4o_mini["model_display"] == "GPT-4o Mini"
    assert r_4o_mini["best_practices_md"]

    assert r_4["model_key"] == "gpt4"
    assert r_4["model_display"] == "GPT-4"
    assert r_4["best_practices_md"]
