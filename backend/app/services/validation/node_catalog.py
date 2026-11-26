import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional


def _find_node_definitions_path() -> Path:
    """Locate shared/node_definitions.json relative to the backend package."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "shared" / "node_definitions.json"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("Could not locate shared/node_definitions.json")


@lru_cache(maxsize=1)
def load_node_definitions() -> Dict[str, Dict[str, Any]]:
    """Load and index supported node definitions by their canonical type name."""
    path = _find_node_definitions_path()
    with path.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)

    definitions: Dict[str, Dict[str, Any]] = {}
    for entry in raw.get("nodeTypes", []):
        node_type = entry.get("type")
        if node_type:
            definitions[node_type] = entry
    return definitions


def get_supported_node_types() -> List[str]:
    """Return the list of canonical supported node types."""
    return list(load_node_definitions().keys())


def get_node_definition(node_type: Optional[str]) -> Optional[Dict[str, Any]]:
    """Return the definition dict for a given node type, or None if unsupported."""
    if not node_type:
        return None
    return load_node_definitions().get(node_type)
