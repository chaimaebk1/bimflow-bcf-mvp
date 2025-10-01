"""Utilities for reading BCF archives."""
from __future__ import annotations

import os
import posixpath
import zipfile
from typing import Dict, List, Tuple
from xml.etree import ElementTree as ET


TopicDict = Dict[str, object]
ProjectMeta = Dict[str, str]


def _strip_namespace(tag: str) -> str:
    """Return the XML tag name without the namespace part."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _get_direct_text(element: ET.Element, name: str) -> str | None:
    """Return the text of a direct child matching ``name`` ignoring namespaces."""
    for child in element:
        if _strip_namespace(child.tag).lower() == name.lower():
            if child.text is None:
                return None
            return child.text.strip() or None
    return None


def _parse_version(xml_bytes: bytes) -> str | None:
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return None

    candidates = [root, *root.iter()]
    for candidate in candidates:
        if _strip_namespace(candidate.tag).lower() == "versioninfo":
            return (
                candidate.get("DetailedVersion")
                or candidate.get("VersionId")
                or candidate.get("Version")
                or (candidate.text.strip() if candidate.text else None)
            )
    return None


def _parse_project_name(xml_bytes: bytes) -> str | None:
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return None

    candidates = [root, *root.iter()]
    for candidate in candidates:
        tag = _strip_namespace(candidate.tag).lower()
        if tag in {"projectinfo", "project"}:
            name = (
                candidate.get("Name")
                or candidate.get("ProjectName")
                or _get_direct_text(candidate, "Name")
                or _get_direct_text(candidate, "ProjectName")
            )
            if name:
                return name
    return None


def _parse_comment(comment_elem: ET.Element) -> Dict[str, str | None]:
    return {
        "guid": comment_elem.get("Guid") or _get_direct_text(comment_elem, "Guid"),
        "author": comment_elem.get("Author")
        or comment_elem.get("CreationAuthor")
        or _get_direct_text(comment_elem, "Author")
        or _get_direct_text(comment_elem, "CreationAuthor"),
        "createdAt": comment_elem.get("Date")
        or comment_elem.get("CreationDate")
        or _get_direct_text(comment_elem, "Date")
        or _get_direct_text(comment_elem, "CreationDate"),
        "comment": _get_direct_text(comment_elem, "Comment"),
        "viewpointGuid": comment_elem.get("ViewpointGuid")
        or _get_direct_text(comment_elem, "ViewpointGuid"),
    }


def _parse_viewpoints(root: ET.Element) -> List[Dict[str, str | None]]:
    viewpoint_parent = None
    for child in root:
        if _strip_namespace(child.tag).lower() == "viewpoints":
            viewpoint_parent = child
            break
    if viewpoint_parent is None and _strip_namespace(root.tag).lower() == "viewpoints":
        viewpoint_parent = root

    candidates: List[ET.Element] = []
    if viewpoint_parent is not None:
        candidates.extend(
            elem
            for elem in viewpoint_parent
            if _strip_namespace(elem.tag).lower() == "viewpoint"
        )
    else:
        for elem in root.findall('.//*'):
            if _strip_namespace(elem.tag).lower() == "viewpoint":
                has_child_data = any(
                    _strip_namespace(child.tag).lower() in {"viewpoint", "snapshot", "orthogonalcamera", "perspectivecamera"}
                    for child in elem
                )
                if has_child_data:
                    candidates.append(elem)

    viewpoints: List[Dict[str, str | None]] = []
    for viewpoint_elem in candidates:
        guid = viewpoint_elem.get("Guid") or _get_direct_text(viewpoint_elem, "Guid")
        viewpoint_file = _get_direct_text(viewpoint_elem, "Viewpoint")
        snapshot_file = _get_direct_text(viewpoint_elem, "Snapshot")
        index = viewpoint_elem.get("Index") or _get_direct_text(viewpoint_elem, "Index")
        viewpoints.append(
            {
                "guid": guid,
                "viewpoint": viewpoint_file,
                "snapshot": snapshot_file,
                "index": index,
            }
        )
    return viewpoints


def _parse_topic(xml_bytes: bytes) -> TopicDict:
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return {
            "guid": None,
            "title": None,
            "status": None,
            "priority": None,
            "author": None,
            "createdAt": None,
            "comments": [],
            "viewpoints": [],
            "snapshot": None,
        }

    topic_elem = None
    if _strip_namespace(root.tag).lower() == "topic":
        topic_elem = root
    else:
        for child in root.findall('.//*'):
            if _strip_namespace(child.tag).lower() == "topic":
                topic_elem = child
                break

    topic_dict: TopicDict = {
        "guid": None,
        "title": None,
        "status": None,
        "priority": None,
        "author": None,
        "createdAt": None,
        "comments": [],
        "viewpoints": [],
        "snapshot": None,
    }

    if topic_elem is not None:
        topic_dict["guid"] = (
            topic_elem.get("Guid")
            or topic_elem.get("guid")
            or _get_direct_text(topic_elem, "Guid")
        )
        topic_dict["title"] = (
            topic_elem.get("Title")
            or _get_direct_text(topic_elem, "Title")
        )
        topic_dict["status"] = (
            topic_elem.get("Status")
            or _get_direct_text(topic_elem, "Status")
        )
        topic_dict["priority"] = (
            topic_elem.get("Priority")
            or _get_direct_text(topic_elem, "Priority")
        )
        topic_dict["author"] = (
            topic_elem.get("CreationAuthor")
            or topic_elem.get("Author")
            or _get_direct_text(topic_elem, "CreationAuthor")
            or _get_direct_text(topic_elem, "Author")
        )
        topic_dict["createdAt"] = (
            topic_elem.get("CreationDate")
            or topic_elem.get("CreatedDate")
            or _get_direct_text(topic_elem, "CreationDate")
            or _get_direct_text(topic_elem, "CreatedDate")
        )

    comments_parent = None
    if _strip_namespace(root.tag).lower() == "comments":
        comments_parent = root
    else:
        for child in root:
            if _strip_namespace(child.tag).lower() == "comments":
                comments_parent = child
                break
    comment_elements: List[ET.Element] = []
    if comments_parent is not None:
        comment_elements.extend(
            elem
            for elem in comments_parent
            if _strip_namespace(elem.tag).lower() == "comment"
        )
    else:
        comment_elements.extend(
            elem
            for elem in root.findall('.//*')
            if _strip_namespace(elem.tag).lower() == "comment"
        )

    topic_dict["comments"] = [_parse_comment(elem) for elem in comment_elements]

    viewpoints = _parse_viewpoints(root if topic_elem is None else root)
    topic_dict["viewpoints"] = viewpoints

    for vp in viewpoints:
        if vp.get("snapshot"):
            topic_dict["snapshot"] = vp["snapshot"]
            break

    return topic_dict


def _resolve_zip_path(base: str, relative: str | None) -> str | None:
    if not relative:
        return None
    relative = relative.strip()
    if not relative:
        return None
    if relative.startswith("/"):
        return relative.lstrip("/")
    if not base:
        return relative
    return posixpath.normpath(posixpath.join(base, relative))


def _resolve_dir_path(root_dir: str, topic_dir: str, relative: str | None) -> str | None:
    """Resolve a relative file reference within a directory based BCF archive."""
    if not relative:
        return None
    relative = relative.strip()
    if not relative:
        return None

    # Handle absolute-like references by interpreting them relative to the archive root
    if relative.startswith(("/", "\\")):
        candidate = os.path.join(root_dir, relative.lstrip("/\\"))
    else:
        candidate = os.path.join(topic_dir, relative)

    candidate = os.path.normpath(candidate)
    rel_to_root = os.path.relpath(candidate, root_dir)
    rel_posix = posixpath.normpath(rel_to_root.replace(os.sep, "/"))
    return rel_posix


def _read_bcf_from_zip(bcf_path: str) -> Tuple[ProjectMeta, List[TopicDict]]:
    """Read a BCF archive stored as a ZIP file."""
    project_meta: ProjectMeta = {}
    topics: List[TopicDict] = []

    with zipfile.ZipFile(bcf_path) as archive:
        names = set(archive.namelist())

        version_file = next(
            (name for name in names if name.lower().endswith("bcf.version")),
            None,
        )
        if version_file:
            version = _parse_version(archive.read(version_file))
            if version:
                project_meta["bcfVersion"] = version

        project_file = next(
            (name for name in names if name.lower().endswith("project.bcfp")),
            None,
        )
        if project_file:
            project_name = _parse_project_name(archive.read(project_file))
            if project_name:
                project_meta["projectName"] = project_name

        topic_files = [
            name
            for name in names
            if name.lower().endswith("markup.bcf") or name.lower().endswith("topic.bcf")
        ]

        for topic_file in sorted(topic_files):
            topic_dir = posixpath.dirname(topic_file)
            topic_data = _parse_topic(archive.read(topic_file))

            if not topic_data.get("guid"):
                topic_data["guid"] = posixpath.basename(topic_dir)

            resolved_viewpoints = []
            topic_snapshot_path = _resolve_zip_path(topic_dir, topic_data.get("snapshot"))
            topic_snapshot_data: bytes | None = None
            for vp in topic_data.get("viewpoints", []):
                resolved = dict(vp)
                viewpoint_path = _resolve_zip_path(topic_dir, vp.get("viewpoint"))
                snapshot_path = _resolve_zip_path(topic_dir, vp.get("snapshot"))

                resolved["viewpoint"] = viewpoint_path
                resolved["snapshot"] = snapshot_path

                if viewpoint_path and viewpoint_path in names:
                    try:
                        resolved["viewpointData"] = archive.read(viewpoint_path)
                    except KeyError:
                        pass

                if snapshot_path and snapshot_path in names:
                    try:
                        snapshot_bytes = archive.read(snapshot_path)
                    except KeyError:
                        snapshot_bytes = None
                    else:
                        resolved["snapshotData"] = snapshot_bytes
                        if topic_snapshot_path is None:
                            topic_snapshot_path = snapshot_path
                        if topic_snapshot_data is None:
                            topic_snapshot_data = snapshot_bytes

                resolved_viewpoints.append(resolved)
            topic_data["viewpoints"] = resolved_viewpoints

            if topic_snapshot_path:
                topic_data["snapshot"] = topic_snapshot_path
            else:
                for vp in resolved_viewpoints:
                    if vp.get("snapshot"):
                        topic_data["snapshot"] = vp["snapshot"]
                        topic_snapshot_path = vp.get("snapshot")
                        topic_snapshot_data = vp.get("snapshotData")
                        break

            if topic_snapshot_path and topic_snapshot_path in names and topic_snapshot_data is None:
                try:
                    topic_snapshot_data = archive.read(topic_snapshot_path)
                except KeyError:
                    topic_snapshot_data = None

            if topic_snapshot_data is not None:
                topic_data["snapshotData"] = topic_snapshot_data

            topics.append(topic_data)

    return project_meta, topics


def _read_bcf_from_dir(bcf_dir: str) -> Tuple[ProjectMeta, List[TopicDict]]:
    """Read a BCF archive stored as an extracted directory."""
    project_meta: ProjectMeta = {}
    topics: List[TopicDict] = []

    try:
        entries = os.listdir(bcf_dir)
    except FileNotFoundError:
        return project_meta, topics

    # Read project level metadata files if they exist
    for entry in entries:
        entry_path = os.path.join(bcf_dir, entry)
        lower_entry = entry.lower()
        if os.path.isfile(entry_path):
            if lower_entry.endswith("bcf.version"):
                try:
                    with open(entry_path, "rb") as fh:
                        version = _parse_version(fh.read())
                except OSError:
                    version = None
                if version:
                    project_meta["bcfVersion"] = version
            elif lower_entry.endswith("project.bcfp"):
                try:
                    with open(entry_path, "rb") as fh:
                        project_name = _parse_project_name(fh.read())
                except OSError:
                    project_name = None
                if project_name:
                    project_meta["projectName"] = project_name

    topic_dirs = [
        entry
        for entry in entries
        if os.path.isdir(os.path.join(bcf_dir, entry))
    ]

    for topic_name in sorted(topic_dirs):
        topic_path = os.path.join(bcf_dir, topic_name)
        try:
            topic_entries = os.listdir(topic_path)
        except OSError:
            continue

        topic_file_path = None
        for entry in sorted(topic_entries):
            if entry.lower().endswith("markup.bcf") or entry.lower().endswith("topic.bcf"):
                topic_file_path = os.path.join(topic_path, entry)
                break

        if not topic_file_path:
            continue

        try:
            with open(topic_file_path, "rb") as fh:
                topic_bytes = fh.read()
        except OSError:
            continue

        topic_data = _parse_topic(topic_bytes)

        if not topic_data.get("guid"):
            topic_data["guid"] = topic_name

        resolved_viewpoints = []
        topic_snapshot_path = _resolve_dir_path(
            bcf_dir, topic_path, topic_data.get("snapshot")
        )
        topic_snapshot_data: bytes | None = None
        for vp in topic_data.get("viewpoints", []):
            resolved = dict(vp)
            viewpoint_path = _resolve_dir_path(bcf_dir, topic_path, vp.get("viewpoint"))
            snapshot_path = _resolve_dir_path(bcf_dir, topic_path, vp.get("snapshot"))

            resolved["viewpoint"] = viewpoint_path
            resolved["snapshot"] = snapshot_path

            if viewpoint_path:
                abs_viewpoint = os.path.join(bcf_dir, viewpoint_path.replace("/", os.sep))
                if os.path.isfile(abs_viewpoint):
                    try:
                        with open(abs_viewpoint, "rb") as fh:
                            resolved["viewpointData"] = fh.read()
                    except OSError:
                        pass

            if snapshot_path:
                abs_snapshot = os.path.join(bcf_dir, snapshot_path.replace("/", os.sep))
                if os.path.isfile(abs_snapshot):
                    try:
                        with open(abs_snapshot, "rb") as fh:
                            snapshot_bytes = fh.read()
                    except OSError:
                        snapshot_bytes = None
                    else:
                        resolved["snapshotData"] = snapshot_bytes
                        if topic_snapshot_path is None:
                            topic_snapshot_path = snapshot_path
                        if topic_snapshot_data is None:
                            topic_snapshot_data = snapshot_bytes

            resolved_viewpoints.append(resolved)
        topic_data["viewpoints"] = resolved_viewpoints

        if topic_snapshot_path:
            topic_data["snapshot"] = topic_snapshot_path
        else:
            for vp in resolved_viewpoints:
                if vp.get("snapshot"):
                    topic_data["snapshot"] = vp["snapshot"]
                    topic_snapshot_path = vp.get("snapshot")
                    topic_snapshot_data = vp.get("snapshotData")
                    break

        if topic_snapshot_path and topic_snapshot_data is None:
            abs_snapshot = os.path.join(
                bcf_dir, topic_snapshot_path.replace("/", os.sep)
            )
            if os.path.isfile(abs_snapshot):
                try:
                    with open(abs_snapshot, "rb") as fh:
                        topic_snapshot_data = fh.read()
                except OSError:
                    topic_snapshot_data = None

        if topic_snapshot_data is not None:
            topic_data["snapshotData"] = topic_snapshot_data

        topics.append(topic_data)

    return project_meta, topics


def read_bcf(bcf_path: str) -> Tuple[ProjectMeta, List[TopicDict]]:
    """Read a BCF 2.1/3.0 archive and extract metadata and topics."""

    if zipfile.is_zipfile(bcf_path):
        return _read_bcf_from_zip(bcf_path)

    if os.path.isdir(bcf_path) or bcf_path.lower().endswith(".bcf"):
        return _read_bcf_from_dir(bcf_path)

    # Not a valid BCF archive path; return empty structures for resilience.
    return {}, []
