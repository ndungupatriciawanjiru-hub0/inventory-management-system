"""Thin client for the OpenFoodFacts API.

Responses are normalised into the same shape we store in our inventory,
so the Flask app and the CLI never deal with raw OpenFoodFacts JSON.
"""
import requests

BASE_URL = "https://world.openfoodfacts.org"
HEADERS = {"User-Agent": "InventoryManagementSystem/1.0 (student-project)"}
TIMEOUT = 10  # seconds


class ExternalAPIError(Exception):
    """Raised when OpenFoodFacts is unreachable or returns bad data."""


def _normalise(product: dict, barcode: str = None) -> dict:
    """Pick the fields we care about out of a raw OpenFoodFacts product."""
    return {
        "product_name": product.get("product_name") or "Unknown product",
        "brands": product.get("brands", ""),
        "ingredients_text": product.get("ingredients_text", ""),
        "barcode": barcode or product.get("code", ""),
    }


def fetch_by_barcode(barcode: str):
    """Return a normalised product dict, or None if the barcode is unknown."""
    try:
        resp = requests.get(
            f"{BASE_URL}/api/v2/product/{barcode}.json",
            headers=HEADERS, timeout=TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        raise ExternalAPIError(f"OpenFoodFacts request failed: {exc}") from exc

    if data.get("status") != 1 or "product" not in data:
        return None
    return _normalise(data["product"], barcode)


def search_by_name(name: str, limit: int = 5):
    """Return a list of normalised products matching a name (maybe empty)."""
    try:
        resp = requests.get(
            f"{BASE_URL}/cgi/search.pl",
            params={"search_terms": name, "search_simple": 1,
                    "action": "process", "json": 1, "page_size": limit},
            headers=HEADERS, timeout=TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        raise ExternalAPIError(f"OpenFoodFacts request failed: {exc}") from exc

    return [_normalise(p) for p in data.get("products", [])][:limit]