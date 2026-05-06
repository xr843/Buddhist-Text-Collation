from __future__ import annotations

import importlib

from sqlalchemy.orm import configure_mappers


def test_auth_admin_collab_modules_are_importable():
    """Documented auth/admin/collab modules must import before they can be routed."""
    for module_name in [
        "app.api.v1.auth.routes",
        "app.api.v1.admin.routes",
        "app.api.v1.collab.project_routes",
        "app.api.v1.collab.share_routes",
    ]:
        importlib.import_module(module_name)

    configure_mappers()


def test_auth_admin_collab_routes_are_registered(client):
    """Documented auth/admin/collab APIs should appear in the generated schema."""
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]

    assert "/api/v1/auth/register" in paths
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/auth/me" in paths
    assert "/api/v1/admin/users" in paths
    assert "/api/v1/admin/stats" in paths
    assert "/api/v1/collab/projects" in paths
    assert "/api/v1/collab/projects/shared" in paths
    assert "/api/v1/collab/projects/{project_id}/members" in paths
