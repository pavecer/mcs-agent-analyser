"""Shared utility functions used across multiple modules."""

import re
import zipfile
from pathlib import Path


def sanitize_yaml(text: str) -> str:
    """Fix YAML that contains characters PyYAML can't handle."""
    # Replace tabs with spaces (YAML spec disallows tabs for indentation, but they appear in values too)
    text = text.replace("\t", "    ")
    # Quote bare keys starting with @ (e.g. `@odata.type: String` -> `"@odata.type": String`)
    text = re.sub(r"^(\s*)(@[a-zA-Z0-9_.]+)(\s*:)", r'\1"\2"\3', text, flags=re.MULTILINE)
    # Quote bare values starting with @ (e.g. `displayName: @mention tag` -> `displayName: "@mention tag"`)
    text = re.sub(r"(:\s+)(@[^\n]+)$", lambda m: m.group(1) + '"' + m.group(2) + '"', text, flags=re.MULTILINE)
    return text


def safe_temp_path(base_dir: str | Path, filename: str | None, default_name: str) -> Path:
    """Build a temp path from an untrusted filename without allowing path injection."""
    candidate = Path(filename or "").name
    if not candidate:
        candidate = default_name
    return Path(base_dir) / candidate


def is_zip_filename(filename: str | None) -> bool:
    """Return True when the provided filename has a .zip suffix."""
    return Path(filename or "").suffix.lower() == ".zip"


def zip_has_agent_assets(names: list[str]) -> bool:
    """Return True when a ZIP listing contains a bots directory at any depth."""
    for name in names:
        normalized = name.strip("/")
        if not normalized:
            continue
        if normalized == "bots":
            return True
        if "/bots/" in f"/{normalized}/":
            return True
    return False


def find_solution_root(extracted_root: Path) -> Path | None:
    """Find directory containing solution.xml in extracted ZIP content.

    Supports archives where files are at root as well as wrapped in one top-level
    folder (common when zipping an extracted directory manually).
    """
    direct = extracted_root / "solution.xml"
    if direct.exists():
        return extracted_root

    candidates = [p.parent for p in extracted_root.rglob("solution.xml") if p.is_file()]
    if not candidates:
        return None

    return min(candidates, key=lambda p: len(p.relative_to(extracted_root).parts))


def safe_extractall(zf: zipfile.ZipFile, dest: Path) -> None:
    """Extract a ZIP, rejecting any entries that would escape *dest* via path traversal."""
    dest_resolved = dest.resolve()
    for info in zf.infolist():
        if Path(info.filename).is_absolute():
            raise ValueError(f"Rejected unsafe ZIP entry: {info.filename!r}")
        if info.filename.endswith("/"):
            continue
        mode = (info.external_attr >> 16) & 0o170000
        if mode == 0o120000:
            raise ValueError(f"Rejected symlink ZIP entry: {info.filename!r}")
        target = (dest_resolved / info.filename).resolve()
        if not target.is_relative_to(dest_resolved):
            raise ValueError(f"Rejected unsafe ZIP entry: {info.filename!r}")
    zf.extractall(dest)
