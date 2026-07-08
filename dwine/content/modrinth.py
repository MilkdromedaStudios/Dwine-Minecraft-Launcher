"""Modrinth API v2 client.

Modrinth is Dwine's content source: every mod, resource pack and shader
is fetched from its official API with sha512 verification. Nothing is
rehosted, nothing is patched.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from ..core.http import get_json

API = "https://api.modrinth.com/v2"


@dataclass
class ProjectHit:
    slug: str
    title: str
    description: str
    downloads: int
    project_type: str
    categories: list[str] = field(default_factory=list)
    icon_url: str = ""


@dataclass
class VersionFile:
    url: str
    filename: str
    sha512: str
    size: int
    primary: bool


@dataclass
class ProjectVersion:
    id: str
    project_id: str
    name: str
    version_number: str
    game_versions: list[str]
    loaders: list[str]
    files: list[VersionFile]
    dependencies: list[dict[str, Any]] = field(default_factory=list)

    @property
    def primary_file(self) -> VersionFile:
        for file in self.files:
            if file.primary:
                return file
        return self.files[0]


def search(
    query: str,
    project_type: str = "mod",
    game_version: str | None = None,
    loader: str | None = None,
    limit: int = 20,
) -> list[ProjectHit]:
    facets: list[list[str]] = [[f"project_type:{project_type}"]]
    if game_version:
        facets.append([f"versions:{game_version}"])
    if loader and project_type == "mod":
        facets.append([f"categories:{loader}"])
    data = get_json(
        f"{API}/search",
        params={
            "query": query,
            "facets": json.dumps(facets),
            "limit": limit,
            "index": "relevance",
        },
    )
    return [
        ProjectHit(
            slug=hit["slug"],
            title=hit["title"],
            description=hit.get("description", ""),
            downloads=hit.get("downloads", 0),
            project_type=hit.get("project_type", project_type),
            categories=hit.get("categories", []),
            icon_url=hit.get("icon_url") or "",
        )
        for hit in data.get("hits", [])
    ]


def get_project(slug: str) -> dict[str, Any] | None:
    from requests import HTTPError

    try:
        return get_json(f"{API}/project/{slug}")
    except HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None
        raise


def _parse_version(raw: dict[str, Any]) -> ProjectVersion:
    return ProjectVersion(
        id=raw["id"],
        project_id=raw["project_id"],
        name=raw.get("name", ""),
        version_number=raw.get("version_number", ""),
        game_versions=raw.get("game_versions", []),
        loaders=raw.get("loaders", []),
        files=[
            VersionFile(
                url=f["url"],
                filename=f["filename"],
                sha512=f.get("hashes", {}).get("sha512", ""),
                size=f.get("size", 0),
                primary=f.get("primary", False),
            )
            for f in raw.get("files", [])
        ],
        dependencies=raw.get("dependencies", []),
    )


def get_versions(
    slug: str,
    game_version: str | None = None,
    loader: str | None = None,
) -> list[ProjectVersion]:
    """Compatible versions of a project, newest first."""
    params: dict[str, str] = {}
    if game_version:
        params["game_versions"] = json.dumps([game_version])
    if loader:
        params["loaders"] = json.dumps([loader])
    raw = get_json(f"{API}/project/{slug}/version", params=params)
    return [_parse_version(v) for v in raw]


def best_version(
    slug: str,
    game_version: str,
    loader: str | None = None,
) -> ProjectVersion | None:
    """Newest version matching the game version (and loader, when relevant)."""
    versions = get_versions(slug, game_version=game_version, loader=loader)
    if versions:
        return versions[0]
    # Resource packs / shaders sometimes omit loader tags; retry without.
    if loader:
        versions = get_versions(slug, game_version=game_version)
        return versions[0] if versions else None
    return None


def get_version_by_id(version_id: str) -> ProjectVersion:
    return _parse_version(get_json(f"{API}/version/{version_id}"))
