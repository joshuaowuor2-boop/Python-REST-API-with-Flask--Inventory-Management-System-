# Python REST API with Flask — Inventory Management System

A Flask REST API and CLI for managing retail inventory, with product enrichment from the [OpenFoodFacts](https://world.openfoodfacts.org/) API. Built as a Summative Lab covering Flask CRUD routes, an external API integration, a CLI client, and a pytest test suite.

## Contents

- [Setup](#setup)
- [Running the API](#running-the-api)
- [Data model](#data-model)
- [API reference](#api-reference)
- [CLI usage](#cli-usage)
- [Running tests](#running-tests)
- [Project structure](#project-structure)

## Setup

```console
$ pipenv install
$ pipenv shell
```

This installs `flask`, `requests`, and `pytest` (see `Pipfile`).

## Running the API

```console
$ python app.py
```

The API runs at `http://localhost:5000` in debug mode. Storage is an in-memory Python list (`storage.py`) seeded with four sample products — restarting the server resets the data.

## Data model

Each inventory item is a dict shaped like an OpenFoodFacts product plus retail fields:

```json
{
  "id": 1,
  "product_name": "Organic Almond Milk",
  "brands": "Silk",
  "barcode": "0025293001156",
  "category": "Dairy Alternatives",
  "ingredients_text": "Filtered water, almonds, cane sugar, sea salt, ...",
  "image_url": null,
  "price": 4.99,
  "quantity_in_stock": 25,
  "source": "manual"
}
```

`source` is `"manual"` for items added directly and `"openfoodfacts"` for items imported from the external API.

## API reference

| Method | Route | Body / Query | Response |
|---|---|---|---|
| GET | `/inventory` | — | `200` list of all items |
| GET | `/inventory/<id>` | — | `200` item, `404` if not found |
| POST | `/inventory` | JSON: `product_name`, `price` required; `brands`, `barcode`, `category`, `ingredients_text`, `image_url`, `quantity_in_stock` optional | `201` created item, `400` if required fields missing |
| PATCH | `/inventory/<id>` | JSON: any subset of item fields (e.g. `price`, `quantity_in_stock`) | `200` updated item, `404` if not found |
| DELETE | `/inventory/<id>` | — | `204` on success, `404` if not found |
| GET | `/inventory/lookup` | query `barcode=` or `name=` | `200` normalized OpenFoodFacts result(s) — does **not** touch inventory storage; `404` no match; `400` no param given; `502` OpenFoodFacts unreachable |
| POST | `/inventory/import` | JSON: `barcode` or `name` | `201` — fetches from OpenFoodFacts and appends the result to inventory; same error codes as `/lookup` |

### Examples

```console
$ curl http://localhost:5000/inventory
$ curl -X POST http://localhost:5000/inventory \
    -H "Content-Type: application/json" \
    -d '{"product_name": "Peanut Butter", "brands": "Jif", "price": 3.49, "quantity_in_stock": 10}'
$ curl -X PATCH http://localhost:5000/inventory/1 \
    -H "Content-Type: application/json" -d '{"price": 5.49}'
$ curl "http://localhost:5000/inventory/lookup?barcode=3017620422003"
$ curl -X POST http://localhost:5000/inventory/import \
    -H "Content-Type: application/json" -d '{"barcode": "3017620422003"}'
```

## CLI usage

With the API running (`python app.py`), in another terminal:

```console
$ python cli.py list
$ python cli.py view 1
$ python cli.py add --name "Peanut Butter" --brand Jif --price 3.49 --quantity 10
$ python cli.py update 1 --price 5.49 --quantity 30
$ python cli.py delete 2
$ python cli.py find --barcode 3017620422003
$ python cli.py find --name nutella
$ python cli.py import --barcode 3017620422003
```

Pass `--base-url` (or set the `INVENTORY_API_URL` environment variable) to point the CLI at a different host. Run `python cli.py -h` or `python cli.py <command> -h` for full option lists. Unreachable servers, 404s, and invalid input (e.g. a non-numeric `--price`) all produce a clean error message and a non-zero exit code instead of a traceback.

## Running tests

```console
$ pytest
```

External HTTP calls (OpenFoodFacts and the CLI's calls to the Flask API) are mocked with `unittest.mock` so the test suite never depends on network access.

## Project structure

```
app.py               Flask app: CRUD routes + OpenFoodFacts lookup/import routes
storage.py            In-memory inventory list + CRUD helpers, seeded with sample data
external_api.py       OpenFoodFacts client (fetch_by_barcode, search_by_name)
cli.py                 argparse-based CLI client for the API
testing/
  conftest.py           Shared fixtures (Flask test client, storage reset between tests)
  test_app.py            REST endpoint tests
  test_external_api.py   OpenFoodFacts client tests
  test_cli.py             CLI tests
```
