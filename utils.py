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
