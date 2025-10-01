"""Tools for merging multiple BCF archives into a single file."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
import tempfile
from typing import Dict, List, Optional, Set, Tuple

from . import reader


TopicDict = Dict[str, object]
ProjectMeta = Dict[str, str]


def _is_empty(value: object) -> bool:
    """Return ``True`` if ``value`` should be considered empty."""
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    return False


def _comment_key(comment: Dict[str, object]) -> Tuple[str, str, str]:
    """Return a tuple used to de-duplicate comments."""
    author = str(comment.get("author") or "").strip()
    created_at = str(
        comment.get("date") or comment.get("createdAt") or ""
    ).strip()
    text = str(comment.get("text") or comment.get("comment") or "").strip()
    return author, created_at, text


def _viewpoint_key(viewpoint: Dict[str, object]) -> Tuple[str, str, str, str]:
    """Return a tuple representing a viewpoint for deduplication."""
    return (
        str(viewpoint.get("guid") or ""),
        str(viewpoint.get("viewpoint") or ""),
        str(viewpoint.get("snapshot") or ""),
        str(viewpoint.get("index") or ""),
    )


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None

    candidate = value.strip()
    if not candidate:
        return None

    candidate = candidate.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(candidate)
    except ValueError:
        pass

    # Fallbacks for common datetime strings that ``fromisoformat`` does not handle.
    for fmt in (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(candidate.split(".")[0], fmt)
        except ValueError:
            continue

    return None


@dataclass
class _AggregatedTopic:
    data: TopicDict
    comment_keys: Set[Tuple[str, str, str]]
    viewpoint_keys: Set[Tuple[str, str, str, str]]
    snapshot_timestamp: Optional[datetime]


def _as_dict_list(values: object) -> List[Dict[str, object]]:
    if not isinstance(values, list):
        return []
    return [deepcopy(item) for item in values if isinstance(item, dict)]


def _viewpoint_dicts(topic: TopicDict) -> List[Dict[str, object]]:
    details = topic.get("_viewpointDetails")
    if isinstance(details, list):
        return [deepcopy(item) for item in details if isinstance(item, dict)]
    return _as_dict_list(topic.get("viewpoints"))


def _stringify_viewpoints(viewpoints: List[Dict[str, object]]) -> List[str]:
    result: List[str] = []
    for viewpoint in viewpoints:
        for key in ("viewpoint", "snapshot", "guid", "index"):
            value = viewpoint.get(key)
            if isinstance(value, str) and value.strip():
                result.append(value.strip())
                break
    return result


def _initialise_topic(topic: TopicDict) -> _AggregatedTopic:
    topic_copy: TopicDict = deepcopy(topic)

    comments = _as_dict_list(topic_copy.get("comments"))
    topic_copy["comments"] = comments

    viewpoints = _viewpoint_dicts(topic_copy)
    topic_copy["_viewpointDetails"] = viewpoints
    topic_copy["viewpoints"] = _stringify_viewpoints(viewpoints)

    return _AggregatedTopic(
        data=topic_copy,
        comment_keys={_comment_key(comment) for comment in comments},
        viewpoint_keys={_viewpoint_key(vp) for vp in viewpoints},
        snapshot_timestamp=_parse_datetime(str(topic_copy.get("createdAt") or "")),
    )


def _merge_topic(base: _AggregatedTopic, incoming: TopicDict) -> None:
    """Merge ``incoming`` topic data into ``base`` in-place."""
    # Complete empty scalar fields with data from the incoming topic.
    for key, value in incoming.items():
        if key in {"comments", "viewpoints"}:
            continue
        if key not in base.data or _is_empty(base.data.get(key)):
            base.data[key] = deepcopy(value)

    # Merge comments, deduplicating by author/date/comment text.
    for comment in _as_dict_list(incoming.get("comments")):
        key = _comment_key(comment)
        if key in base.comment_keys:
            continue
        base.comment_keys.add(key)
        base.data.setdefault("comments", []).append(comment)

    # Merge viewpoints. Keep all distinct combinations.
    for viewpoint in _viewpoint_dicts(incoming):
        key = _viewpoint_key(viewpoint)
        if key in base.viewpoint_keys:
            continue
        base.viewpoint_keys.add(key)
        base.data.setdefault("_viewpointDetails", []).append(deepcopy(viewpoint))
        base.data["viewpoints"] = _stringify_viewpoints(
            _viewpoint_dicts(base.data)
        )

    # Update snapshot with the most recent topic creation date.
    incoming_timestamp = _parse_datetime(str(incoming.get("createdAt") or ""))
    incoming_snapshot = incoming.get("snapshot")
    if incoming_snapshot:
        if base.data.get("snapshot") is None:
            base.data["snapshot"] = deepcopy(incoming_snapshot)
            base.snapshot_timestamp = incoming_timestamp or base.snapshot_timestamp
        else:
            if base.snapshot_timestamp is None or (
                incoming_timestamp is not None and incoming_timestamp > base.snapshot_timestamp
            ):
                base.data["snapshot"] = deepcopy(incoming_snapshot)
                base.snapshot_timestamp = incoming_timestamp or base.snapshot_timestamp


def merge_bcfs(paths: List[str], out_path: Optional[str] = None) -> str:
    """Merge multiple BCF archives into a single archive.

    Parameters
    ----------
    paths:
        Paths to the source BCF archives that should be merged.
    out_path:
        Destination path for the resulting merged BCF archive. When omitted,
        a temporary ``.bcfzip`` file is created and its path is returned.
    """

    if not paths:
        raise ValueError("At least one BCF path is required to perform a merge.")

    from . import writer  # Imported lazily to avoid import cycles during type checking.

    merged_meta: ProjectMeta = {}
    aggregated_topics: Dict[str, _AggregatedTopic] = {}
    topic_order: List[str] = []

    for path_index, bcf_path in enumerate(paths):
        project_meta, topics = reader.read_bcf(bcf_path)

        # Complete project metadata with the first non-empty value encountered per key.
        for key, value in project_meta.items():
            if _is_empty(merged_meta.get(key)) and not _is_empty(value):
                merged_meta[key] = str(value)

        for topic_index, topic in enumerate(topics):
            if not isinstance(topic, dict):
                continue

            guid = topic.get("guid")
            if not guid:
                guid = f"__missing_guid__{path_index}_{topic_index}"

            if guid not in aggregated_topics:
                aggregated_topics[guid] = _initialise_topic(topic)
                topic_order.append(guid)
            else:
                _merge_topic(aggregated_topics[guid], topic)

    merged_topics: List[TopicDict] = [aggregated_topics[guid].data for guid in topic_order]

    output_path = out_path
    if output_path is None:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".bcfzip")
        tmp.close()
        output_path = tmp.name

    writer.write_bcf(output_path, merged_meta, merged_topics)

    return output_path
