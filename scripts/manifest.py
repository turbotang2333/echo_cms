"""Validate the non-secret deployment contract shared by project repositories."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml


ALLOWED_KINDS = {"static", "web", "compose", "ai-api"}
APP_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]{2,62}$")
DOMAIN_PATTERN = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$"
)
PATH_PREFIX_PATTERN = re.compile(r"^/[A-Za-z0-9._~/-]*$")


class ManifestError(ValueError):
    """Raised when a deployment manifest is unsafe or incomplete."""


def _require_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{key} must be a non-empty string")
    return value.strip()


def validate_manifest(path: Path) -> dict[str, Any]:
    """Return normalized public deployment values from a YAML manifest."""

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ManifestError(f"cannot read manifest: {error}") from error
    except yaml.YAMLError as error:
        raise ManifestError(f"invalid YAML: {error}") from error

    if not isinstance(data, dict):
        raise ManifestError("manifest must be a mapping")

    app_id = _require_string(data, "id")
    if not APP_ID_PATTERN.fullmatch(app_id) or "--" in app_id or app_id.endswith("-"):
        raise ManifestError("id must use lowercase letters, digits, and single hyphens")

    kind = _require_string(data, "kind")
    if kind not in ALLOWED_KINDS:
        raise ManifestError(f"kind must be one of: {', '.join(sorted(ALLOWED_KINDS))}")

    domain = _require_string(data, "domain").lower()
    if not DOMAIN_PATTERN.fullmatch(domain):
        raise ManifestError("domain must be a valid lowercase fully qualified domain name")

    path_prefix = data.get("pathPrefix", "/")
    if not isinstance(path_prefix, str) or not path_prefix.strip():
        raise ManifestError("pathPrefix must be a non-empty string")
    path_prefix = path_prefix.strip()
    if (
        not PATH_PREFIX_PATTERN.fullmatch(path_prefix)
        or "\n" in path_prefix
        or "\r" in path_prefix
        or " " in path_prefix
        or "//" in path_prefix
        or "/../" in path_prefix
        or path_prefix.endswith("/..")
    ):
        raise ManifestError("pathPrefix must be an absolute safe URL path")
    if path_prefix != "/" and not path_prefix.endswith("/"):
        raise ManifestError("pathPrefix must end with /")

    port = data.get("internalPort")
    if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
        raise ManifestError("internalPort must be an integer between 1 and 65535")

    health_path = _require_string(data, "healthPath")
    if not health_path.startswith("/") or "\n" in health_path or "\r" in health_path:
        raise ManifestError("healthPath must be an absolute single-line path")

    return {
        "app_id": app_id,
        "kind": kind,
        "domain": domain,
        "path_prefix": path_prefix,
        "internal_port": port,
        "health_path": health_path,
    }


def write_github_output(path: Path, manifest: dict[str, Any]) -> None:
    """Write only validated, non-secret values in GitHub Actions output format."""

    keys = ("app_id", "kind", "domain", "path_prefix", "internal_port", "health_path")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(f"{key}={manifest[key]}\n" for key in keys), encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--github-output", type=Path)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args(argv)

    try:
        manifest = validate_manifest(args.manifest)
    except ManifestError as error:
        print(f"deployment manifest error: {error}", file=sys.stderr)
        return 2

    if args.github_output:
        write_github_output(args.github_output, manifest)
    else:
        for key, value in manifest.items():
            print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
