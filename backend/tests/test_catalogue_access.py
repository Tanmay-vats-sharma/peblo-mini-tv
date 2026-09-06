from pathlib import Path

from fastapi.testclient import TestClient

from app.database import get_db
from app.models import Show


def test_viewer_can_access_public_catalogue_routes(
    client: TestClient,
    auth_headers: dict[str, dict],
):
    catalogue = client.get("/catalog", headers=auth_headers["viewer"])
    search = client.get("/catalog/search", headers=auth_headers["viewer"])

    assert catalogue.status_code == 200
    assert search.status_code == 200


def test_editor_cannot_publish_catalogue(
    client: TestClient,
    auth_headers: dict[str, dict],
):
    response = client.post(
        "/admin/catalog/publish",
        headers=auth_headers["editor"],
    )
    assert response.status_code == 403


def test_admin_publish_blocks_invalid_catalogue_without_replacing_file(
    client: TestClient,
    auth_headers: dict[str, dict],
    monkeypatch,
    tmp_path: Path,
):
    from app.services import catalogue_service

    catalogue_path = tmp_path / "catalogue.json"
    catalogue_path.write_text('{"existing": true}', encoding="utf-8")
    monkeypatch.setattr(catalogue_service, "CATALOGUE_PATH", catalogue_path)
    monkeypatch.setattr(catalogue_service, "CATALOGUE_DIR", tmp_path)

    db_generator = client.app.dependency_overrides[get_db]()
    db = next(db_generator)
    try:
        db.add(
            Show(
                title="Invalid Published Show",
                slug="invalid-published-show",
                categories=[],
                is_published=True,
                section=None,
            )
        )
        db.commit()
    finally:
        db.close()

    response = client.post(
        "/admin/catalog/publish",
        headers=auth_headers["admin"],
    )

    assert response.status_code == 200
    assert response.json()["status"] == "blocked"
    assert catalogue_path.read_text(encoding="utf-8") == '{"existing": true}'
