"""Tests for CLI commands; the HTTP layer (requests) is mocked."""
from unittest.mock import MagicMock, patch

import requests

import cli

ITEM = {"id": 1, "product_name": "Milk", "brands": "Silk", "price": 3.0,
        "stock": 5, "barcode": "1", "ingredients_text": "water"}


def _resp(body, status=200):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = body
    return r


@patch("cli.requests.request", return_value=_resp([ITEM]))
def test_list(mock_req, capsys):
    assert cli.main(["list"]) == 0
    assert "Milk" in capsys.readouterr().out
    assert mock_req.call_args[0][:2] == ("GET", f"{cli.API_URL}/inventory")


@patch("cli.requests.request", return_value=_resp(ITEM))
def test_view(mock_req, capsys):
    assert cli.main(["view", "1"]) == 0
    assert "Milk" in capsys.readouterr().out


@patch("cli.requests.request", return_value=_resp({"error": "Item not found"}, 404))
def test_view_not_found(mock_req, capsys):
    assert cli.main(["view", "9"]) == 1
    assert "Item not found" in capsys.readouterr().err


@patch("cli.requests.request", return_value=_resp(ITEM, 201))
def test_add_sends_payload(mock_req):
    assert cli.main(["add", "Milk", "--price", "3", "--stock", "5"]) == 0
    payload = mock_req.call_args.kwargs["json"]
    assert payload["product_name"] == "Milk" and payload["stock"] == 5


@patch("cli.requests.request", return_value=_resp(ITEM))
def test_update(mock_req):
    assert cli.main(["update", "1", "--price", "4.5"]) == 0
    assert mock_req.call_args.kwargs["json"] == {"price": 4.5}


def test_update_requires_a_field(capsys):
    assert cli.main(["update", "1"]) == 1
    assert "Nothing to update" in capsys.readouterr().err


@patch("cli.requests.request", return_value=_resp({"message": "Item deleted"}))
def test_delete(mock_req, capsys):
    assert cli.main(["delete", "1"]) == 0
    assert "Deleted" in capsys.readouterr().out


@patch("cli.requests.request", return_value=_resp([ITEM]))
def test_find_by_barcode(mock_req, capsys):
    assert cli.main(["find", "--barcode", "1"]) == 0
    assert mock_req.call_args.kwargs["params"] == {"barcode": "1"}


def test_find_requires_argument(capsys):
    assert cli.main(["find"]) == 1


@patch("cli.requests.request", return_value=_resp({"error": "Product not found"}, 404))
def test_import_failure(mock_req, capsys):
    assert cli.main(["import", "000"]) == 1


@patch("cli.requests.request", return_value=_resp(ITEM, 201))
def test_import_success(mock_req, capsys):
    assert cli.main(["import", "1", "--stock", "5"]) == 0


@patch("cli.requests.request", side_effect=requests.ConnectionError())
def test_server_down(mock_req, capsys):
    assert cli.main(["list"]) == 1
    assert "Cannot reach API" in capsys.readouterr().err