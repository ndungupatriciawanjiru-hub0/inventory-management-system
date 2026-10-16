"""Tests for the OpenFoodFacts client using mocked HTTP responses."""
from unittest.mock import MagicMock, patch

import pytest
import requests

import openfoodfacts as off


def _resp(json_data, status=200):
    r = MagicMock()
    r.json.return_value = json_data
    r.status_code = status
    r.raise_for_status.side_effect = (
        requests.HTTPError("bad") if status >= 400 else None)
    return r


@patch("openfoodfacts.requests.get")
def test_fetch_by_barcode_success(mock_get):
    mock_get.return_value = _resp({"status": 1, "product": {
        "product_name": "Organic Almond Milk", "brands": "Silk",
        "ingredients_text": "Filtered water, almonds"}})
    p = off.fetch_by_barcode("025293600744")
    assert p["product_name"] == "Organic Almond Milk"
    assert p["barcode"] == "025293600744"


@patch("openfoodfacts.requests.get")
def test_fetch_by_barcode_not_found(mock_get):
    mock_get.return_value = _resp({"status": 0})
    assert off.fetch_by_barcode("000") is None


@patch("openfoodfacts.requests.get", side_effect=requests.ConnectionError("x"))
def test_fetch_by_barcode_network_error(mock_get):
    with pytest.raises(off.ExternalAPIError):
        off.fetch_by_barcode("1")


@patch("openfoodfacts.requests.get")
def test_fetch_by_barcode_http_error(mock_get):
    mock_get.return_value = _resp({}, status=500)
    with pytest.raises(off.ExternalAPIError):
        off.fetch_by_barcode("1")


@patch("openfoodfacts.requests.get")
def test_search_by_name(mock_get):
    mock_get.return_value = _resp({"products": [
        {"product_name": "A", "brands": "X", "code": "1"},
        {"product_name": "B", "brands": "Y", "code": "2"}]})
    results = off.search_by_name("a", limit=1)
    assert len(results) == 1 and results[0]["barcode"] == "1"


@patch("openfoodfacts.requests.get")
def test_search_by_name_invalid_json(mock_get):
    r = _resp({})
    r.json.side_effect = ValueError("not json")
    mock_get.return_value = r
    with pytest.raises(off.ExternalAPIError):
        off.search_by_name("a")