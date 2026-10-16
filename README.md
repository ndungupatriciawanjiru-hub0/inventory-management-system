# Inventory Management System

An administrator portal backend for a small retail company: a Flask REST API
for inventory CRUD, OpenFoodFacts integration, a CLI frontend, and a pytest suite.

## Project structure

```
app.py              Flask REST API + in-memory "mock database" (a list)
openfoodfacts.py    OpenFoodFacts client (barcode / name lookup)
cli.py              Command-line interface that talks to the API
tests/              pytest suite (API, CLI, external API) using unittest.mock
requirements.txt
```

## Installation and setup

```bash
git clone <your-repo-url> && cd inventory-management-system
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py                   # starts the API on http://127.0.0.1:5000 (debug mode)
```

Keep the server running, then use the CLI from a second terminal.
Set `INVENTORY_API_URL` if the server runs elsewhere.

## Data model

Each item in the array looks like:

```json
{
  "id": 1,
  "product_name": "Organic Almond Milk",
  "brands": "Silk",
  "ingredients_text": "Filtered water, almonds, cane sugar",
  "barcode": "025293600744",
  "price": 3.99,
  "stock": 25
}
```

## API endpoints

| Method | Route | Description | Success | Errors |
|--------|-------|-------------|---------|--------|
| GET | `/inventory` | Fetch all items | 200 | |
| GET | `/inventory/<id>` | Fetch one item | 200 | 404 |
| POST | `/inventory` | Add item (`product_name` required; `price`, `stock`, `brands`, `barcode`, `ingredients_text` optional) | 201 | 400 |
| PATCH | `/inventory/<id>` | Update any fields (e.g. `price`, `stock`) | 200 | 400, 404 |
| DELETE | `/inventory/<id>` | Remove item | 200 | 404 |
| GET | `/external/search?barcode=...` or `?name=...` | Look up OpenFoodFacts | 200 | 400, 502 |
| POST | `/inventory/import` | Fetch by `barcode` from OpenFoodFacts and add (optional `price`, `stock`) | 201 | 400, 404, 502 |
| GET | `/health` | Health check | 200 | |

Errors return JSON: `{"error": "message"}`. `502` means OpenFoodFacts failed.

Example with curl:

```bash
curl -X PATCH http://127.0.0.1:5000/inventory/1 \
     -H "Content-Type: application/json" -d '{"price": 4.25, "stock": 10}'
```

## CLI usage

```bash
python cli.py list
python cli.py view 1
python cli.py add "Oat Milk" --brands Alpro --price 3.5 --stock 20
python cli.py update 1 --price 4.25 --stock 10
python cli.py delete 2
python cli.py find --barcode 3017620422003     # search OpenFoodFacts by barcode
python cli.py find --name "almond milk"         # search OpenFoodFacts by name
python cli.py import 3017620422003 --price 4.5 --stock 30   # fetch + add to inventory
```

## Running tests

```bash
pytest -v
```

External HTTP calls are mocked with `unittest.mock`, so tests run offline.

## Debugging

`python app.py` runs Flask in debug mode (auto-reload, tracebacks). Import the
routes into Postman using the table above to validate responses manually.

## Notes

Storage is an in-memory list, so data resets when the server restarts.