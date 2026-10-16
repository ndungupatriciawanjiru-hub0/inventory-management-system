"""Tests for the Flask endpoints (external API is mocked)."""
from unittest.mock import patch

from openfoodfacts import ExternalAPIError

FAKE = {"product_name": "Fake Cola", "brands": "Acme",
        "ingredients_text": "Water, sugar", "barcode": "123"}


def test_get_all(client):
    r = client.get("/inventory")
    assert r.status_code == 200 and len(r.get_json()) == 3


def test_get_one(client):
    assert client.get("/inventory/1").get_json()["product_name"] == "Organic Almond Milk"


def test_get_one_missing(client):
    assert client.get("/inventory/999").status_code == 404


def test_post_creates_item(client):
    r = client.post("/inventory", json={"product_name": "Tea", "price": 2, "stock": 5})
    assert r.status_code == 201
    assert r.get_json()["id"] == 4
    assert len(client.get("/inventory").get_json()) == 4


def test_post_requires_name(client):
    assert client.post("/inventory", json={"price": 2}).status_code == 400


def test_post_rejects_bad_price_and_stock(client):
    assert client.post("/inventory", json={"product_name": "x", "price": -1}).status_code == 400
    assert client.post("/inventory", json={"product_name": "x", "stock": 1.5}).status_code == 400


def test_post_rejects_non_json(client):
    assert client.post("/inventory", data="nope").status_code == 400


def test_patch_updates_price_and_stock(client):
    r = client.patch("/inventory/1", json={"price": 9.5, "stock": 3})
    assert r.status_code == 200
    assert r.get_json()["price"] == 9.5 and r.get_json()["stock"] == 3


def test_patch_cannot_change_id(client):
    r = client.patch("/inventory/1", json={"id": 50})
    assert r.status_code == 400
    assert client.get("/inventory/1").get_json()["id"] == 1


def test_patch_rejects_empty_body(client):
    r = client.patch("/inventory/1", json={})
    assert r.status_code == 400 and "No fields" in r.get_json()["error"]


def test_patch_rejects_unknown_field(client):
    r = client.patch("/inventory/1", json={"colour": "red"})
    assert r.status_code == 400 and "colour" in r.get_json()["error"]


def test_patch_rejects_blank_or_non_string_name(client):
    assert client.patch("/inventory/1", json={"product_name": "  "}).status_code == 400
    assert client.patch("/inventory/1", json={"product_name": 5}).status_code == 400


def test_patch_can_rename(client):
    r = client.patch("/inventory/1", json={"product_name": "Oat Milk"})
    assert r.status_code == 200 and r.get_json()["product_name"] == "Oat Milk"


def test_patch_missing_and_invalid(client):
    assert client.patch("/inventory/999", json={"price": 1}).status_code == 404
    assert client.patch("/inventory/1", json={"price": "free"}).status_code == 400


def test_delete(client):
    assert client.delete("/inventory/1").status_code == 200
    assert client.get("/inventory/1").status_code == 404


def test_delete_missing(client):
    assert client.delete("/inventory/999").status_code == 404


@patch("app.openfoodfacts.fetch_by_barcode", return_value=FAKE)
def test_external_search_barcode(mock_fetch, client):
    r = client.get("/external/search?barcode=123")
    assert r.status_code == 200 and r.get_json()[0]["product_name"] == "Fake Cola"


@patch("app.openfoodfacts.search_by_name", return_value=[FAKE])
def test_external_search_name(mock_search, client):
    assert client.get("/external/search?name=cola").status_code == 200


def test_external_search_needs_param(client):
    assert client.get("/external/search").status_code == 400


@patch("app.openfoodfacts.fetch_by_barcode", side_effect=ExternalAPIError("down"))
def test_external_search_failure_returns_502(mock_fetch, client):
    assert client.get("/external/search?barcode=1").status_code == 502


@patch("app.openfoodfacts.fetch_by_barcode", return_value=dict(FAKE))
def test_import_adds_to_inventory(mock_fetch, client):
    r = client.post("/inventory/import", json={"barcode": "123", "price": 1.2, "stock": 7})
    assert r.status_code == 201
    assert r.get_json()["product_name"] == "Fake Cola" and r.get_json()["stock"] == 7
    assert len(client.get("/inventory").get_json()) == 4


@patch("app.openfoodfacts.fetch_by_barcode", return_value=None)
def test_import_unknown_barcode(mock_fetch, client):
    assert client.post("/inventory/import", json={"barcode": "0"}).status_code == 404


def test_import_requires_barcode(client):
    assert client.post("/inventory/import", json={}).status_code == 400
