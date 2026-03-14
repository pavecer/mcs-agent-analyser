from __future__ import annotations

import io
import zipfile

from solution_checker import check_solution_zip


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
