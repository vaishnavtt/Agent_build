"""Security utilities for workflow execution: path validation, SSRF protection, redaction, and auth."""

import ipaddress
import os
import re
import socket
from pathlib import Path
from typing import Any, Dict, Iterable, Optional
from urllib.parse import urlparse

from app.core.config import settings
from app.engine.types import NodeExecutionError, ToolExecutionError


_SENSITIVE_KEY_PARTS = (
    "key",
    "secret",
    "token",
    "password",
    "passwd",
    "authorization",
    "cookie",
    "credential",
    "apikey",
    "api_key",
)

_ALLOWED_DOC_EXTENSIONS = {".pdf", ".txt", ".md", ".json", ".csv"}

_SECRET_URL_RE = re.compile(r"([?&](?:key|api_key|token|access_token|secret)=)([^&\s]+)", re.IGNORECASE)
_BEARER_RE = re.compile(r"(Bearer\s+)[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE)


def redact_text(text: str) -> str:
    """Scrubs API keys and bearer tokens from log or error strings."""
    if not text:
        return text
    cleaned = _SECRET_URL_RE.sub(r"\1[REDACTED]", text)
    cleaned = _BEARER_RE.sub(r"\1[REDACTED]", cleaned)
    return cleaned


def redact_sensitive_data(data: Any) -> Any:
    """Recursively redacts sensitive fields from dictionaries and lists."""
    if isinstance(data, dict):
        sanitized: Dict[str, Any] = {}
        for k, v in data.items():
            k_lower = str(k).lower()
            if any(part in k_lower for part in _SENSITIVE_KEY_PARTS):
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = redact_sensitive_data(v)
        return sanitized
    if isinstance(data, list):
        return [redact_sensitive_data(item) for item in data]
    if isinstance(data, str):
        return redact_text(data)
    return data


def get_allowed_document_roots() -> list[Path]:
    """Returns resolved directories from which Document Reader may read local files."""
    configured = getattr(settings, "ALLOWED_DOCUMENT_DIRS", None)
    roots: list[Path] = []
    if configured:
        for item in configured:
            roots.append(Path(item).resolve())
    else:
        backend_dir = Path(__file__).resolve().parents[2]
        roots.append((backend_dir / "uploads").resolve())
        roots.append((Path.cwd() / "uploads").resolve())
    return roots


def validate_document_path(file_path: str, node_id: str = "", node_name: str = "Document Reader") -> Path:
    """Validates that a local document path stays within allowed roots and has a safe extension."""
    if not file_path or "\x00" in file_path:
        raise NodeExecutionError(
            f"Invalid document path provided in node '{node_name}'.",
            node_id=node_id,
        )

    raw_parts = Path(file_path).parts
    if ".." in raw_parts:
        raise NodeExecutionError(
            f"Path traversal is not permitted in node '{node_name}'.",
            node_id=node_id,
        )

    try:
        resolved = Path(file_path).resolve()
    except Exception as exc:
        raise NodeExecutionError(
            f"Unable to resolve document path in node '{node_name}': {exc}",
            node_id=node_id,
        )

    allowed_roots = get_allowed_document_roots()
    in_allowed_root = False
    for root in allowed_roots:
        try:
            resolved.relative_to(root)
            in_allowed_root = True
            break
        except ValueError:
            continue

    if not in_allowed_root:
        raise NodeExecutionError(
            f"Access denied: document path '{file_path}' is outside allowed document directories.",
            node_id=node_id,
        )

    if resolved.suffix.lower() not in _ALLOWED_DOC_EXTENSIONS:
        raise NodeExecutionError(
            f"Unsupported document extension '{resolved.suffix}' in node '{node_name}'.",
            node_id=node_id,
        )

    if not resolved.exists() or not resolved.is_file():
        raise NodeExecutionError(
            f"Document not found at '{file_path}' in node '{node_name}'.",
            node_id=node_id,
        )

    return resolved


def _is_forbidden_ip(ip_str: str) -> bool:
    """Returns True if the IP address is private, loopback, link-local, multicast, or reserved."""
    try:
        ip_obj = ipaddress.ip_address(ip_str)
    except ValueError:
        return True

    if isinstance(ip_obj, ipaddress.IPv6Address) and ip_obj.ipv4_mapped is not None:
        ip_obj = ip_obj.ipv4_mapped

    return (
        ip_obj.is_private
        or ip_obj.is_loopback
        or ip_obj.is_link_local
        or ip_obj.is_multicast
        or ip_obj.is_reserved
        or ip_obj.is_unspecified
    )


def validate_outbound_url(url: str) -> str:
    """Validates an outbound HTTP/HTTPS URL and blocks SSRF targets (localhost, private IPs, metadata)."""
    if not url or not isinstance(url, str):
        raise ToolExecutionError("HTTP request requires a non-empty URL.")

    parsed = urlparse(url.strip())
    if parsed.scheme.lower() not in ("http", "https"):
        raise ToolExecutionError(f"Unsupported URL scheme '{parsed.scheme}'. Only http and https are allowed.")

    hostname = (parsed.hostname or "").strip().lower()
    if not hostname:
        raise ToolExecutionError("HTTP request URL is missing a valid hostname.")

    if hostname in ("localhost", "localhost.localdomain") or hostname.endswith((".local", ".internal")):
        raise ToolExecutionError(f"Outbound requests to internal host '{hostname}' are blocked.")

    # Direct IP literal check
    try:
        ipaddress.ip_address(hostname)
        if _is_forbidden_ip(hostname):
            raise ToolExecutionError(f"Outbound requests to private or local IP '{hostname}' are blocked.")
        return url.strip()
    except ValueError:
        pass

    # Resolve hostname and verify all returned IPs are public
    try:
        addr_info = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror as exc:
        raise ToolExecutionError(f"Could not resolve hostname '{hostname}': {exc}")

    if not addr_info:
        raise ToolExecutionError(f"No DNS records found for hostname '{hostname}'.")

    for entry in addr_info:
        resolved_ip = entry[4][0]
        if _is_forbidden_ip(resolved_ip):
            raise ToolExecutionError(
                f"Outbound requests to '{hostname}' resolved to restricted IP '{resolved_ip}'."
            )

    return url.strip()
