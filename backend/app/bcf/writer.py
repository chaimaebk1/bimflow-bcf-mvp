"""Utilities for writing BCF archives."""
from __future__ import annotations

import base64
import posixpath
import re
import zipfile
from binascii import Error as BinasciiError
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from xml.etree import ElementTree as ET

TopicDict = Dict[str, object]
ProjectMeta = Dict[str, str]

_BLANK_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/xcAAwMB/6Xl3V8AAAAASUVORK5CYII="
)


def _sanitize_segment(value: str, fallback: str) -> str:
    """Return a filesystem-safe segment suitable for inclusion in a ZIP archive."""
    candidate = re.sub(r"[^A-Za-z0-9._-]", "_", value).strip("./")
    if not candidate:
        return fallback
    if candidate in {".", ".."}:
        return fallback
    return candidate


def _xml_bytes(element: ET.Element) -> bytes:
    return ET.tostring(element, encoding="utf-8", xml_declaration=True)


def _coerce_str(value: object) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    return str(value)


def _coerce_bytes(value: object) -> Optional[bytes]:
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return b""
        try:
            return base64.b64decode(text, validate=True)
        except (BinasciiError, ValueError):
            return text.encode("utf-8")
    return None


def _pick_first_bytes(container: Dict[str, object], keys: Sequence[str]) -> Optional[bytes]:
    for key in keys:
        if key in container:
            data = _coerce_bytes(container[key])
            if data is not None:
                return data
    return None


def _default_viewpoint_xml(guid: Optional[str]) -> bytes:
    root = ET.Element("VisualizationInfo")
    if guid:
        root.set("Guid", guid)
    return _xml_bytes(root)


def _build_version_xml(version: str) -> bytes:
    root = ET.Element("Version")
    if version:
        root.set("VersionId", version)
    detailed = ET.SubElement(root, "DetailedVersion")
    detailed.text = version
    return _xml_bytes(root)


def _build_project_xml(project_name: str) -> bytes:
    root = ET.Element("ProjectExtension")
    project = ET.SubElement(root, "Project")
    project.set("Name", project_name)
    return _xml_bytes(root)


def _build_comments(parent: ET.Element, comments: Iterable[Dict[str, object]]) -> None:
    comments_list = [comment for comment in comments if isinstance(comment, dict)]
    if not comments_list:
        return

    container = ET.SubElement(parent, "Comments")
    for comment in comments_list:
        elem = ET.SubElement(container, "Comment")

        guid = _coerce_str(comment.get("guid"))
        if guid:
            elem.set("Guid", guid)

        created_at = _coerce_str(comment.get("date") or comment.get("createdAt"))
        if created_at:
            date = ET.SubElement(elem, "Date")
            date.text = created_at

        author = _coerce_str(comment.get("author"))
        if author:
            author_elem = ET.SubElement(elem, "Author")
            author_elem.text = author

        comment_text = _coerce_str(comment.get("text") or comment.get("comment"))
        if comment_text:
            text_elem = ET.SubElement(elem, "Comment")
            text_elem.text = comment_text

        viewpoint_guid = _coerce_str(comment.get("viewpointGuid"))
        if viewpoint_guid:
            viewpoint_elem = ET.SubElement(elem, "Viewpoint")
            viewpoint_elem.set("Guid", viewpoint_guid)


def _unique_name(base_name: str, existing: set[str]) -> str:
    if base_name not in existing:
        existing.add(base_name)
        return base_name

    stem, dot, suffix = base_name.partition(".")
    counter = 1
    while True:
        candidate = f"{stem}_{counter}" + (f".{suffix}" if dot else "")
        if candidate not in existing:
            existing.add(candidate)
            return candidate
        counter += 1


def write_bcf(out_path: str, project_meta: dict, topics: List[dict]) -> None:
    """Serialise BCF data into a ``.bcfzip`` archive."""

    project_meta = dict(project_meta or {})
    topics = list(topics or [])

    version = _coerce_str(project_meta.get("bcfVersion")) or "2.1"
    project_name = _coerce_str(project_meta.get("projectName"))

    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("bcf.version", _build_version_xml(version))

        if project_name:
            archive.writestr("project.bcfp", _build_project_xml(project_name))

        used_topic_dirs: set[str] = set()

        for index, topic in enumerate(topics):
            if not isinstance(topic, dict):
                continue

            topic_guid = _coerce_str(topic.get("guid"))
            if not topic_guid:
                topic_guid = f"topic_{index + 1:04d}"

            folder_name = _sanitize_segment(topic_guid, f"topic_{index + 1:04d}")
            if folder_name in used_topic_dirs:
                base_name = folder_name
                counter = 1
                while f"{base_name}_{counter}" in used_topic_dirs:
                    counter += 1
                folder_name = f"{base_name}_{counter}"
            used_topic_dirs.add(folder_name)
            topic_dir = folder_name

            title = _coerce_str(topic.get("title"))
            status = _coerce_str(topic.get("status"))
            priority = _coerce_str(topic.get("priority"))
            author = _coerce_str(topic.get("author"))
            created_at = _coerce_str(topic.get("createdAt"))

            markup_root = ET.Element("Markup")
            topic_elem = ET.SubElement(markup_root, "Topic")
            topic_elem.set("Guid", topic_guid)

            if status:
                topic_elem.set("TopicStatus", status)
            if title:
                title_elem = ET.SubElement(topic_elem, "Title")
                title_elem.text = title
            if priority:
                priority_elem = ET.SubElement(topic_elem, "Priority")
                priority_elem.text = priority
            if created_at:
                creation_elem = ET.SubElement(topic_elem, "CreationDate")
                creation_elem.text = created_at
            if author:
                author_elem = ET.SubElement(topic_elem, "CreationAuthor")
                author_elem.text = author

            _build_comments(markup_root, topic.get("comments", []))

            viewpoints_input = [
                vp
                for vp in topic.get("_viewpointDetails", [])
                if isinstance(vp, dict)
            ]

            topic_snapshot_bytes = _pick_first_bytes(
                topic,
                (
                    "snapshotData",
                    "snapshotBinary",
                    "snapshotContent",
                    "snapshotBytes",
                    "snapshotImage",
                ),
            )

            attachments: List[Tuple[str, bytes]] = []
            used_names: set[str] = set()
            viewpoints_elem = None

            if not viewpoints_input:
                viewpoints_input = [{}]

            for vp_index, vp in enumerate(viewpoints_input, start=1):
                vp_guid = _coerce_str(vp.get("guid"))
                vp_index_value = _coerce_str(vp.get("index"))

                vp_default_name = f"viewpoint_{vp_index:02d}.bcfv"
                vp_name = _sanitize_segment(
                    posixpath.basename(_coerce_str(vp.get("viewpoint")) or ""),
                    vp_default_name,
                )
                vp_name = _unique_name(vp_name, used_names)

                snapshot_default_name = f"snapshot_{vp_index:02d}.png"
                snapshot_name = None
                raw_snapshot_name = _coerce_str(vp.get("snapshot"))
                if raw_snapshot_name:
                    snapshot_name = _sanitize_segment(
                        posixpath.basename(raw_snapshot_name), snapshot_default_name
                    )
                else:
                    snapshot_name = snapshot_default_name
                snapshot_name = _unique_name(snapshot_name, used_names)

                vp_data = _pick_first_bytes(
                    vp,
                    (
                        "viewpointData",
                        "viewpointBinary",
                        "viewpointContent",
                        "viewpointXml",
                        "viewpointXML",
                    ),
                )
                if vp_data is None:
                    vp_data = _default_viewpoint_xml(vp_guid)

                snapshot_data = _pick_first_bytes(
                    vp,
                    (
                        "snapshotData",
                        "snapshotBinary",
                        "snapshotContent",
                        "snapshotBytes",
                        "snapshotImage",
                    ),
                )
                if snapshot_data is None:
                    snapshot_data = topic_snapshot_bytes
                if snapshot_data is None:
                    snapshot_data = _BLANK_PNG

                attachments.append((vp_name, vp_data))
                attachments.append((snapshot_name, snapshot_data))

                if viewpoints_elem is None:
                    viewpoints_elem = ET.SubElement(markup_root, "Viewpoints")

                vp_elem = ET.SubElement(viewpoints_elem, "Viewpoint")
                if vp_guid:
                    vp_elem.set("Guid", vp_guid)
                if vp_index_value:
                    vp_elem.set("Index", vp_index_value)

                viewpoint_file_elem = ET.SubElement(vp_elem, "Viewpoint")
                viewpoint_file_elem.text = vp_name

                snapshot_file_elem = ET.SubElement(vp_elem, "Snapshot")
                snapshot_file_elem.text = snapshot_name

            markup_bytes = _xml_bytes(markup_root)

            archive.writestr(f"{topic_dir}/markup.bcf", markup_bytes)

            for rel_path, data in attachments:
                archive.writestr(f"{topic_dir}/{rel_path}", data)
