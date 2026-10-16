"""Flask REST API for the inventory management system.

Storage is a simple in-memory list (the "mock database"), seeded with
items that resemble OpenFoodFacts data. Every item has an integer id.
"""
from flask import Flask, jsonify, request

import openfoodfacts
from openfoodfacts import ExternalAPIError

# ---- Mock database ---------------------------------------------------------
SEED_DATA = [
    {"id": 1, "product_name": "Organic Almond Milk", "brands": "Silk",
     "ingredients_text": "Filtered water, almonds, cane sugar",
     "barcode": "025293600744", "price": 3.99, "stock": 25},
    {"id": 2, "product_name": "Nutella", "brands": "Ferrero",
     "ingredients_text": "Sugar, palm oil, hazelnuts, cocoa, skim milk",
     "barcode": "3017620422003", "price": 4.49, "stock": 40},
    {"id": 3, "product_name": "Whole Wheat Bread", "brands": "Nature's Own",
     "ingredients_text": "Whole wheat flour, water, yeast, salt",
     "barcode": "0072250011359", "price": 2.79, "stock": 15},
]

inventory = [dict(item) for item in SEED_DATA]
_next_id = max(i["id"] for i in inventory) + 1


def reset_inventory():
    """Restore the seed data (used by tests)."""
    global inventory, _next_id
    inventory = [dict(item) for item in SEED_DATA]
    _next_id = max(i["id"] for i in inventory) + 1


def _find(item_id):
    return next((i for i in inventory if i["id"] == item_id), None)


def _validate(data, partial=False):
    """Return an error string for bad input, or None if it is fine."""
    if not isinstance(data, dict):
        return "Request body must be a JSON object"
    if not partial and not data.get("product_name"):
        return "'product_name' is required"
    if "price" in data and (not isinstance(data["price"], (int, float))
                            or isinstance(data["price"], bool) or data["price"] < 0):
        return "'price' must be a non-negative number"
    if "stock" in data and (not isinstance(data["stock"], int)
                            or isinstance(data["stock"], bool) or data["stock"] < 0):
        return "'stock' must be a non-negative integer"
    return None


def _add_item(fields):
    """Append a new item to the array and return it."""
    global _next_id
    item = {
        "id": _next_id,
        "product_name": fields.get("product_name", ""),
        "brands": fields.get("brands", ""),
        "ingredients_text": fields.get("ingredients_text", ""),
        "barcode": fields.get("barcode", ""),
        "price": fields.get("price", 0.0),
        "stock": fields.get("stock", 0),
    }
    _next_id += 1
    inventory.append(item)
    return item


def create_app():
    app = Flask(__name__)

    # ---- CRUD routes -------------------------------------------------------
    @app.get("/inventory")
    def get_all():
        return jsonify(inventory), 200

    @app.get("/inventory/<int:item_id>")
    def get_one(item_id):
        item = _find(item_id)
        if item is None:
            return jsonify(error="Item not found"), 404
        return jsonify(item), 200

    @app.post("/inventory")
    def create():
        data = request.get_json(silent=True)
        error = _validate(data)
        if error:
            return jsonify(error=error), 400
        return jsonify(_add_item(data)), 201

    @app.patch("/inventory/<int:item_id>")
    def update(item_id):
        item = _find(item_id)
        if item is None:
            return jsonify(error="Item not found"), 404
        data = request.get_json(silent=True)
        error = _validate(data, partial=True)
        if error:
            return jsonify(error=error), 400
        data.pop("id", None)  # ids are immutable
        item.update({k: v for k, v in data.items() if k in item})
        return jsonify(item), 200

    @app.delete("/inventory/<int:item_id>")
    def delete(item_id):
        item = _find(item_id)
        if item is None:
            return jsonify(error="Item not found"), 404
        inventory.remove(item)
        return jsonify(message="Item deleted", item=item), 200

    # ---- Helper routes (OpenFoodFacts integration) -------------------------
    @app.get("/external/search")
    def external_search():
        """Look up products on OpenFoodFacts by ?barcode= or ?name=."""
        barcode = request.args.get("barcode")
        name = request.args.get("name")
        if not barcode and not name:
            return jsonify(error="Provide 'barcode' or 'name' query parameter"), 400
        try:
            if barcode:
                product = openfoodfacts.fetch_by_barcode(barcode)
                results = [product] if product else []
            else:
                results = openfoodfacts.search_by_name(name)
        except ExternalAPIError as exc:
            return jsonify(error=str(exc)), 502
        return jsonify(results), 200

    @app.post("/inventory/import")
    def import_from_barcode():
        """Fetch a product by barcode and add it to inventory.

        JSON body: {"barcode": "...", "price": 1.5, "stock": 10}
        (price and stock are optional; OpenFoodFacts does not know them).
        """
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or not data.get("barcode"):
            return jsonify(error="'barcode' is required"), 400
        error = _validate(data, partial=True)
        if error:
            return jsonify(error=error), 400
        try:
            product = openfoodfacts.fetch_by_barcode(data["barcode"])
        except ExternalAPIError as exc:
            return jsonify(error=str(exc)), 502
        if product is None:
            return jsonify(error="Product not found on OpenFoodFacts"), 404
        product["price"] = data.get("price", 0.0)
        product["stock"] = data.get("stock", 0)
        return jsonify(_add_item(product)), 201

    @app.get("/health")
    def health():
        return jsonify(status="ok"), 200

    return app


if __name__ == "__main__":
    create_app().run(debug=True)  # Flask debug mode for development