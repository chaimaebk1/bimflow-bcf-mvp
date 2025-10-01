"""Utilities for merging multiple BCF archives."""
from __future__ import annotations

import tempfile
import zipfile
from typing import Iterable


def _increment_component(name: str, counter: int) -> str:
    if "." in name:
        stem, ext = name.rsplit(".", 1)
        return f"{stem}_{counter}.{ext}"
    return f"{name}_{counter}"


def _increment_path(path: str, counter: int) -> str:
    if path.endswith("/"):
        base = path.rstrip("/")
        incremented = _increment_path(base, counter)
        return f"{incremented}/"
    if "/" in path:
        parent, name = path.rsplit("/", 1)
        return f"{parent}/{_increment_component(name, counter)}"
    return _increment_component(path, counter)


def merge_bcfs(bcf_paths: Iterable[str]) -> str:
    """Merge multiple BCF archives into a single temporary archive."""
    paths: list[str] = [path for path in bcf_paths if path]
    if not paths:
        raise ValueError("No BCF archives provided for merging.")

    merged_file = tempfile.NamedTemporaryFile(delete=False, suffix=".bcfzip")
    merged_file.close()

    existing_names: set[str] = set()

    with zipfile.ZipFile(merged_file.name, "w", compression=zipfile.ZIP_DEFLATED) as output_zip:
        for path in paths:
            with zipfile.ZipFile(path, "r") as input_zip:
                for info in input_zip.infolist():
                    name = info.filename
                    candidate = name
                    counter = 1
                    while candidate in existing_names:
                        candidate = _increment_path(name, counter)
                        counter += 1

                    info_copy = zipfile.ZipInfo(filename=candidate, date_time=info.date_time)
                    info_copy.comment = info.comment
                    info_copy.compress_type = info.compress_type
                    info_copy.create_system = info.create_system
                    info_copy.create_version = info.create_version
                    info_copy.extract_version = info.extract_version
                    info_copy.external_attr = info.external_attr
                    info_copy.flag_bits = info.flag_bits
                    info_copy.internal_attr = info.internal_attr
                    info_copy.extra = info.extra
                    info_copy.volume = info.volume

                    data = b""
                    if not info.is_dir():
                        data = input_zip.read(info.filename)

                    output_zip.writestr(info_copy, data)
                    existing_names.add(candidate)

    return merged_file.name
