"""Command-line interface for the inventory API.

Usage examples:
    python cli.py list
    python cli.py add "Oat Milk" --brands Alpro --price 3.5 --stock 20
    python cli.py find --barcode 3017620422003
    python cli.py import 3017620422003 --price 4.5 --stock 30
"""
import argparse
import os
import sys

import requests

API_URL = os.environ.get("INVENTORY_API_URL", "http://127.0.0.1:5000")
TIMEOUT = 15


def _request(method, path, **kwargs):
    """Call the API; return (ok, json_or_error_message)."""
    try:
        resp = requests.request(method, f"{API_URL}{path}", timeout=TIMEOUT, **kwargs)
    except requests.ConnectionError:
        return False, f"Cannot reach API at {API_URL}. Is the server running?"
    except requests.Timeout:
        return False, "The API request timed out."
    try:
        body = resp.json()
    except ValueError:
        return False, f"Unexpected response (HTTP {resp.status_code})"
    if resp.status_code >= 400:
        return False, body.get("error", f"HTTP {resp.status_code}")
    return True, body


def _show(item):
    print(f"[{item['id']}] {item['product_name']} ({item.get('brands') or 'no brand'})")
    print(f"     price: ${item.get('price', 0):.2f}   stock: {item.get('stock', 0)}   "
          f"barcode: {item.get('barcode') or '-'}")
    if item.get("ingredients_text"):
        print(f"     ingredients: {item['ingredients_text']}")


def cmd_list(args):
    ok, body = _request("GET", "/inventory")
    if not ok:
        return _fail(body)
    if not body:
        print("Inventory is empty.")
    for item in body:
        _show(item)
    return 0


def cmd_view(args):
    ok, body = _request("GET", f"/inventory/{args.id}")
    if not ok:
        return _fail(body)
    _show(body)
    return 0


def cmd_add(args):
    payload = {"product_name": args.name, "brands": args.brands or "",
               "barcode": args.barcode or "", "price": args.price, "stock": args.stock}
    ok, body = _request("POST", "/inventory", json=payload)
    if not ok:
        return _fail(body)
    print("Added:")
    _show(body)
    return 0


def cmd_update(args):
    payload = {}
    if args.price is not None:
        payload["price"] = args.price
    if args.stock is not None:
        payload["stock"] = args.stock
    if not payload:
        return _fail("Nothing to update: pass --price and/or --stock")
    ok, body = _request("PATCH", f"/inventory/{args.id}", json=payload)
    if not ok:
        return _fail(body)
    print("Updated:")
    _show(body)
    return 0


def cmd_delete(args):
    ok, body = _request("DELETE", f"/inventory/{args.id}")
    if not ok:
        return _fail(body)
    print(f"Deleted item {args.id}.")
    return 0


def cmd_find(args):
    if not args.barcode and not args.name:
        return _fail("Pass --barcode or --name")
    params = {"barcode": args.barcode} if args.barcode else {"name": args.name}
    ok, body = _request("GET", "/external/search", params=params)
    if not ok:
        return _fail(body)
    if not body:
        print("No products found on OpenFoodFacts.")
    for p in body:
        print(f"- {p['product_name']} ({p.get('brands') or 'no brand'}) "
              f"barcode: {p.get('barcode') or '-'}")
    return 0


def cmd_import(args):
    payload = {"barcode": args.barcode, "price": args.price, "stock": args.stock}
    ok, body = _request("POST", "/inventory/import", json=payload)
    if not ok:
        return _fail(body)
    print("Imported from OpenFoodFacts:")
    _show(body)
    return 0


def _fail(message):
    print(f"Error: {message}", file=sys.stderr)
    return 1


def build_parser():
    parser = argparse.ArgumentParser(description="Inventory management CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List all items").set_defaults(func=cmd_list)

    p = sub.add_parser("view", help="View one item")
    p.add_argument("id", type=int)
    p.set_defaults(func=cmd_view)

    p = sub.add_parser("add", help="Add a new item")
    p.add_argument("name")
    p.add_argument("--brands")
    p.add_argument("--barcode")
    p.add_argument("--price", type=float, default=0.0)
    p.add_argument("--stock", type=int, default=0)
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("update", help="Update price and/or stock")
    p.add_argument("id", type=int)
    p.add_argument("--price", type=float)
    p.add_argument("--stock", type=int)
    p.set_defaults(func=cmd_update)

    p = sub.add_parser("delete", help="Delete an item")
    p.add_argument("id", type=int)
    p.set_defaults(func=cmd_delete)

    p = sub.add_parser("find", help="Search OpenFoodFacts")
    p.add_argument("--barcode")
    p.add_argument("--name")
    p.set_defaults(func=cmd_find)

    p = sub.add_parser("import", help="Fetch by barcode and add to inventory")
    p.add_argument("barcode")
    p.add_argument("--price", type=float, default=0.0)
    p.add_argument("--stock", type=int, default=0)
    p.set_defaults(func=cmd_import)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())