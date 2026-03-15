import tempfile
import zipfile
from pathlib import Path

from deps_analyzer import analyze_deps_zip_bytes_report
from solution_checker import check_solution_zip
from validator import validate_zip_bytes

examples = Path("examples")
for d in sorted(examples.iterdir()):
    if not d.is_dir():
        continue

    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        zip_path = Path(tmp.name)

    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in d.rglob("*"):
                if p.is_file():
                    zf.write(p, p.relative_to(d))

        zip_bytes = zip_path.read_bytes()
        check = check_solution_zip(zip_bytes)
        print(f"[{d.name}] check_error={check.get('error', '')} has_agent_assets={check.get('has_agent_assets')} solution={check.get('solution_name', '')}")

        try:
            deps = analyze_deps_zip_bytes_report(zip_bytes)
            print(f"[{d.name}] deps_ok components={len(deps.get('component_rows', []))} relations={len(deps.get('relation_rows', []))}")
        except Exception as exc:
            print(f"[{d.name}] deps_error={exc}")

        if check.get("has_agent_assets"):
            try:
                val = validate_zip_bytes(zip_bytes)
                print(f"[{d.name}] validate_ok findings={len(val.get('results', []))} model={val.get('model_display', '')}")
            except Exception as exc:
                print(f"[{d.name}] validate_error={exc}")
        else:
            print(f"[{d.name}] validate_skipped_non_agent")
    finally:
        zip_path.unlink(missing_ok=True)
