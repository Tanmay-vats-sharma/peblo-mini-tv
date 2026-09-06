from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image


SHOW_PAYLOAD = {
    "title": "Test Show",
    "slug": "test-show",
    "description": "A test show",
    "section": "series",
    "categories": ["test"],
    "release_year": 2026,
    "is_published": False,
}


def create_show(client: TestClient, headers: dict) -> int:
    response = client.post(
        "/admin/shows",
        json=SHOW_PAYLOAD,
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_season(client: TestClient, headers: dict, show_id: int) -> int:
    response = client.post(
        f"/admin/shows/{show_id}/seasons",
        json={"season_number": 1, "title": "Season One"},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_episode(client: TestClient, headers: dict, season_id: int) -> int:
    response = client.post(
        f"/admin/seasons/{season_id}/episodes",
        json={
            "title": "Episode One",
            "episode_number": 1,
            "content_group": "test-group",
            "language": "en",
            "status": "draft",
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


def image_bytes(size: tuple[int, int], image_format: str = "PNG") -> bytes:
    image = Image.new("RGB", size, color="white")
    output = BytesIO()
    image.save(output, format=image_format)
    return output.getvalue()


def test_login_and_me_for_all_roles(
    client: TestClient,
    tokens: dict[str, str],
):
    assert set(tokens) == {"admin", "editor", "viewer"}

    for role, token in tokens.items():
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["role"] == role
        assert "password_hash" not in response.json()


def test_invalid_login_returns_401(client: TestClient):
    response = client.post(
        "/auth/login",
        json={"email": "admin@example.test", "password": "wrong"},
    )
    assert response.status_code == 401


@pytest.mark.parametrize("method,path_suffix", [
    ("get", ""),
    ("post", ""),
    ("get", "/{show_id}"),
    ("patch", "/{show_id}"),
    ("delete", "/{show_id}"),
])
def test_shows_require_authentication(
    client: TestClient,
    auth_headers: dict[str, dict],
    method: str,
    path_suffix: str,
):
    show_id = create_show(client, auth_headers["admin"])
    path = f"/admin/shows{path_suffix.format(show_id=show_id)}"
    kwargs = {}
    if method == "post":
        kwargs["json"] = SHOW_PAYLOAD | {"slug": "unauthenticated-show"}
    elif method == "patch":
        kwargs["json"] = {"title": "Unauthenticated update"}
    response = getattr(client, method)(path, **kwargs)
    assert response.status_code == 401


def test_show_crud_is_available_to_editor_and_admin(
    client: TestClient,
    auth_headers: dict[str, dict],
):
    for role in ("editor", "admin"):
        show_id = create_show(client, auth_headers[role])
        assert client.get(
            f"/admin/shows/{show_id}",
            headers=auth_headers[role],
        ).status_code == 200
        assert client.patch(
            f"/admin/shows/{show_id}",
            json={"title": f"Updated {role}"},
            headers=auth_headers[role],
        ).status_code == 200
        assert client.delete(
            f"/admin/shows/{show_id}",
            headers=auth_headers[role],
        ).status_code == 204


def test_viewer_cannot_use_show_crud(
    client: TestClient,
    auth_headers: dict[str, dict],
):
    show_id = create_show(client, auth_headers["admin"])
    headers = auth_headers["viewer"]
    assert client.get("/admin/shows", headers=headers).status_code == 403
    assert client.post(
        "/admin/shows", json=SHOW_PAYLOAD | {"slug": "viewer-show"}, headers=headers
    ).status_code == 403
    assert client.patch(
        f"/admin/shows/{show_id}", json={"title": "Denied"}, headers=headers
    ).status_code == 403
    assert client.delete(
        f"/admin/shows/{show_id}", headers=headers
    ).status_code == 403


def test_viewer_cannot_read_a_show(
    client: TestClient,
    auth_headers: dict[str, dict],
):
    show_id = create_show(client, auth_headers["admin"])
    response = client.get(
        f"/admin/shows/{show_id}",
        headers=auth_headers["viewer"],
    )
    assert response.status_code == 403


def test_season_crud_and_duplicate_validation(
    client: TestClient,
    auth_headers: dict[str, dict],
):
    show_id = create_show(client, auth_headers["editor"])
    season_id = create_season(client, auth_headers["editor"], show_id)

    duplicate = client.post(
        f"/admin/shows/{show_id}/seasons",
        json={"season_number": 1, "title": "Duplicate"},
        headers=auth_headers["editor"],
    )
    assert duplicate.status_code == 409
    assert client.get(
        f"/admin/shows/{show_id}/seasons",
        headers=auth_headers["admin"],
    ).status_code == 200
    assert client.get(
        f"/admin/seasons/{season_id}", headers=auth_headers["admin"]
    ).status_code == 200
    assert client.patch(
        f"/admin/seasons/{season_id}",
        json={"title": "Updated Season"},
        headers=auth_headers["admin"],
    ).status_code == 200
    assert client.delete(
        f"/admin/seasons/{season_id}", headers=auth_headers["admin"]
    ).status_code == 204


def test_seasons_reject_unauthenticated_and_viewer(
    client: TestClient,
    auth_headers: dict[str, dict],
):
    show_id = create_show(client, auth_headers["admin"])
    for headers, expected in ((None, 401), (auth_headers["viewer"], 403)):
        request_headers = headers or {}
        response = client.get(
            f"/admin/shows/{show_id}/seasons",
            headers=request_headers,
        )
        assert response.status_code == expected


def test_episode_crud_and_validation(
    client: TestClient,
    auth_headers: dict[str, dict],
):
    show_id = create_show(client, auth_headers["editor"])
    season_id = create_season(client, auth_headers["editor"], show_id)
    episode_id = create_episode(client, auth_headers["editor"], season_id)

    duplicate = client.post(
        f"/admin/seasons/{season_id}/episodes",
        json={
            "title": "Duplicate",
            "episode_number": 2,
            "content_group": "test-group",
            "language": "en",
            "status": "draft",
        },
        headers=auth_headers["editor"],
    )
    assert duplicate.status_code == 409

    invalid_published = client.post(
        f"/admin/seasons/{season_id}/episodes",
        json={
            "title": "Invalid Published",
            "episode_number": 2,
            "content_group": "published-group",
            "language": "hi",
            "status": "published",
        },
        headers=auth_headers["admin"],
    )
    assert invalid_published.status_code == 422
    assert client.get(
        f"/admin/seasons/{season_id}/episodes",
        headers=auth_headers["admin"],
    ).status_code == 200
    assert client.get(
        f"/admin/episodes/{episode_id}", headers=auth_headers["admin"]
    ).status_code == 200
    assert client.patch(
        f"/admin/episodes/{episode_id}",
        json={"title": "Updated Episode"},
        headers=auth_headers["admin"],
    ).status_code == 200
    assert client.delete(
        f"/admin/episodes/{episode_id}", headers=auth_headers["admin"]
    ).status_code == 204


def test_episode_routes_reject_unauthenticated_and_viewer(
    client: TestClient,
    auth_headers: dict[str, dict],
):
    show_id = create_show(client, auth_headers["admin"])
    season_id = create_season(client, auth_headers["admin"], show_id)
    path = f"/admin/seasons/{season_id}/episodes"
    assert client.get(path).status_code == 401
    assert client.get(path, headers=auth_headers["viewer"]).status_code == 403


def test_artwork_upload_permissions_and_validation(
    client: TestClient,
    auth_headers: dict[str, dict],
):
    show_id = create_show(client, auth_headers["admin"])
    path = "/admin/artworks/upload"
    valid_file = {
        "file": ("poster.png", image_bytes((600, 900)), "image/png")
    }
    form = {"show_id": str(show_id), "artwork_type": "poster"}

    assert client.post(path, data=form, files=valid_file).status_code == 401
    assert client.post(
        path, data=form, files=valid_file, headers=auth_headers["viewer"]
    ).status_code == 403
    assert client.post(
        path, data=form, files=valid_file, headers=auth_headers["editor"]
    ).status_code == 201

    invalid_dimensions = {
        "file": ("poster.png", image_bytes((100, 100)), "image/png")
    }
    assert client.post(
        path,
        data=form,
        files=invalid_dimensions,
        headers=auth_headers["admin"],
    ).status_code == 400

    oversized = {"file": ("poster.jpg", b"x" * 200001, "image/jpeg")}
    assert client.post(
        path, data=form, files=oversized, headers=auth_headers["admin"]
    ).status_code == 400

    invalid_type = {"file": ("poster.png", image_bytes((600, 900)), "image/png")}
    assert client.post(
        path,
        data={"show_id": str(show_id), "artwork_type": "unknown"},
        files=invalid_type,
        headers=auth_headers["admin"],
    ).status_code == 422
