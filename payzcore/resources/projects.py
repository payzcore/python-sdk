"""Projects resource for PayzCore API (requires master key)."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..client import HttpClient
from ..types import (
    CreateProjectResponse,
    ListProjectsResponse,
    Project,
    ProjectListItem,
)


def _map_project(raw: Dict[str, Any]) -> Project:
    return {
        "id": raw["id"],
        "name": raw["name"],
        "slug": raw["slug"],
        "api_key": raw["api_key"],
        "webhook_secret": raw["webhook_secret"],
        "webhook_url": raw.get("webhook_url"),
        "created_at": raw["created_at"],
    }


def _map_project_list_item(raw: Dict[str, Any]) -> ProjectListItem:
    return {
        "id": raw["id"],
        "name": raw["name"],
        "slug": raw["slug"],
        "api_key": raw["api_key"],
        "webhook_url": raw.get("webhook_url"),
        "is_active": raw["is_active"],
        "created_at": raw["created_at"],
    }


class Projects:
    """Projects resource (requires master key auth)."""

    def __init__(self, client: HttpClient) -> None:
        self._client = client

    def create(
        self,
        *,
        name: str,
        slug: str,
        webhook_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CreateProjectResponse:
        """Create a new project.

        Args:
            name: Project display name.
            slug: URL-friendly identifier.
            webhook_url: Optional webhook endpoint URL.
            metadata: Optional metadata dict.

        Returns:
            CreateProjectResponse with project details and API key.
        """
        body: Dict[str, Any] = {
            "name": name,
            "slug": slug,
        }
        if webhook_url is not None:
            body["webhook_url"] = webhook_url
        if metadata is not None:
            body["metadata"] = metadata

        raw = self._client.post("/v1/projects", body)
        return {
            "success": True,
            "project": _map_project(raw["project"]),
        }

    def list(self) -> ListProjectsResponse:
        """List all projects.

        Returns:
            ListProjectsResponse with list of projects.
        """
        raw = self._client.get("/v1/projects")
        return {
            "success": True,
            "projects": [_map_project_list_item(p) for p in raw["projects"]],
        }
