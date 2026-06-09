"""Integration tests for the subjects + studio-stats API.

B2 is replaced by an in-memory object store so the routing, manifest
read/write, status transitions, and the privacy purge are all exercised
end-to-end without network or credentials.
"""

import pytest

import app.repo.b2_client as b2
import app.repo.subjects_store as subjects_store
import app.service.stats as stats_service
import app.service.subjects as subjects_service


@pytest.fixture(autouse=True)
def fake_b2(monkeypatch):
    """In-memory stand-in for the B2 object store."""
    store: dict[str, bytes] = {}

    def put_bytes(key, data, content_type):
        store[key] = bytes(data)

    def get_bytes(key):
        return store.get(key)

    def object_exists(key):
        return key in store

    def list_keys(prefix):
        return [k for k in store if k.startswith(prefix)]

    def delete_prefix(prefix):
        victims = [k for k in store if k.startswith(prefix)]
        for k in victims:
            del store[k]
        return len(victims)

    from datetime import UTC, datetime

    from app.types import FileMetadata

    def list_files(prefix="", max_keys=1000):
        out = []
        for k, v in store.items():
            if not k.startswith(prefix):
                continue
            out.append(
                FileMetadata(
                    key=k, filename=k.split("/")[-1], folder="",
                    size_bytes=len(v), size_human=f"{len(v)} B",
                    content_type="application/octet-stream",
                    uploaded_at=datetime.now(UTC),
                )
            )
        return out

    fns = {
        "put_bytes": put_bytes,
        "get_bytes": get_bytes,
        "object_exists": object_exists,
        "list_keys": list_keys,
        "delete_prefix": delete_prefix,
        "list_files": list_files,
    }
    for name, fn in fns.items():
        monkeypatch.setattr(b2, name, fn, raising=False)
    # Patch the already-bound names in every consumer module (they imported
    # the helpers by value, so patching b2_client alone isn't enough).
    for mod in (subjects_store, stats_service, subjects_service):
        for name, fn in fns.items():
            if hasattr(mod, name):
                monkeypatch.setattr(mod, name, fn)
    return store


@pytest.mark.asyncio
async def test_create_list_get_subject(client):
    resp = await client.post("/subjects", json={"name": "Ada"})
    assert resp.status_code == 200
    sid = resp.json()["id"]
    assert resp.json()["status"] == "created"

    listed = await client.get("/subjects")
    assert any(s["id"] == sid for s in listed.json())

    got = await client.get(f"/subjects/{sid}")
    assert got.status_code == 200
    assert got.json()["name"] == "Ada"


@pytest.mark.asyncio
async def test_get_unknown_subject_404(client):
    resp = await client.get("/subjects/" + "a" * 32)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_purge_removes_every_object(client, fake_b2):
    sid = (await client.post("/subjects", json={"name": "Grace"})).json()["id"]
    # seed a few subject-scoped objects of different artifact types
    fake_b2[f"subjects/{sid}/selfies/a.jpg"] = b"x"
    fake_b2[f"subjects/{sid}/headshots/corporate/00.png"] = b"y"

    resp = await client.delete(f"/subjects/{sid}")
    assert resp.status_code == 200
    assert resp.json()["purged"] is True
    # manifest + seeded objects all gone
    assert not any(k.startswith(f"subjects/{sid}/") for k in fake_b2)


@pytest.mark.asyncio
async def test_styles_endpoint_lists_packs(client):
    resp = await client.get("/styles")
    assert resp.status_code == 200
    slugs = {p["slug"] for p in resp.json()}
    assert "corporate" in slugs and "editorial-bw" in slugs


@pytest.mark.asyncio
async def test_generate_requires_trained_model(client):
    sid = (await client.post("/subjects", json={"name": "Lin"})).json()["id"]
    resp = await client.post(
        f"/subjects/{sid}/generate", json={"style_slugs": ["corporate"]}
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_studio_stats_aggregates_by_artifact(client, fake_b2):
    sid = (await client.post("/subjects", json={"name": "Mae"})).json()["id"]
    fake_b2[f"subjects/{sid}/selfies/a.jpg"] = b"123"
    fake_b2[f"subjects/{sid}/headshots/corporate/00.png"] = b"4567"

    resp = await client.get("/stats/studio")
    assert resp.status_code == 200
    data = resp.json()
    assert data["subjects"] >= 1
    assert data["headshots_generated"] >= 1
    cats = {s["category"] for s in data["breakdown"]}
    assert "selfies" in cats and "headshots" in cats
