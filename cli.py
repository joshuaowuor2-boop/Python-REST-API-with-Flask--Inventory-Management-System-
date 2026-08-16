#!/usr/bin/env python3
'''Command-line client for the Inventory Management System REST API.

Run with: python cli.py <command> [options]
'''

import argparse
import os
import sys

import requests

DEFAULT_BASE_URL = os.environ.get('INVENTORY_API_URL', 'http://localhost:5000')


class CLIError(Exception):
    '''Raised for any user-facing failure: unreachable API, bad request, missing item, etc.'''


def _request(method, path, base_url, **kwargs):
    try:
        response = requests.request(method, f'{base_url}{path}', timeout=10, **kwargs)
    except requests.exceptions.RequestException as error:
        raise CLIError(f'Could not reach the inventory API at {base_url}: {error}') from error

    if response.status_code >= 400:
        try:
            message = response.json().get('error', response.text)
        except ValueError:
            message = response.text
        raise CLIError(f'{response.status_code}: {message}')
    return response


def _print_item(item):
    print(f"[{item.get('id')}] {item.get('product_name')} - {item.get('brands') or 'Unknown brand'}")
    print(f"    price: ${item.get('price')}  stock: {item.get('quantity_in_stock')}  barcode: {item.get('barcode')}")


def _print_product(product):
    print(f"{product.get('product_name')} - {product.get('brands') or 'Unknown brand'} (barcode: {product.get('barcode')})")


def cmd_list(args):
    items = _request('GET', '/inventory', args.base_url).json()
    if not items:
        print('Inventory is empty.')
        return
    for item in items:
        _print_item(item)


def cmd_view(args):
    item = _request('GET', f'/inventory/{args.id}', args.base_url).json()
    _print_item(item)


def cmd_add(args):
    payload = {
        'product_name': args.name,
        'brands': args.brand,
        'barcode': args.barcode,
        'category': args.category,
        'price': args.price,
        'quantity_in_stock': args.quantity,
    }
    item = _request('POST', '/inventory', args.base_url, json=payload).json()
    print('Created:')
    _print_item(item)


def cmd_update(args):
    payload = {}
    if args.price is not None:
        payload['price'] = args.price
    if args.quantity is not None:
        payload['quantity_in_stock'] = args.quantity
    if not payload:
        raise CLIError('Provide --price and/or --quantity to update.')
    item = _request('PATCH', f'/inventory/{args.id}', args.base_url, json=payload).json()
    print('Updated:')
    _print_item(item)


def cmd_delete(args):
    _request('DELETE', f'/inventory/{args.id}', args.base_url)
    print(f'Deleted item {args.id}.')


def cmd_find(args):
    params = {'barcode': args.barcode} if args.barcode else {'name': args.name}
    results = _request('GET', '/inventory/lookup', args.base_url, params=params).json()
    results = results if isinstance(results, list) else [results]
    if not results:
        print('No matches found.')
        return
    for product in results:
        _print_product(product)


def cmd_import(args):
    payload = {'barcode': args.barcode} if args.barcode else {'name': args.name}
    item = _request('POST', '/inventory/import', args.base_url, json=payload).json()
    print('Imported:')
    _print_item(item)


def build_parser():
    parser = argparse.ArgumentParser(prog='inventory-cli', description='CLI for the Inventory Management System API.')
    parser.add_argument('--base-url', default=DEFAULT_BASE_URL, help='Base URL of the inventory API (default: %(default)s)')
    subparsers = parser.add_subparsers(dest='command', required=True)

    subparsers.add_parser('list', help='List all inventory items.').set_defaults(func=cmd_list)

    view_parser = subparsers.add_parser('view', help='View a single inventory item.')
    view_parser.add_argument('id', type=int)
    view_parser.set_defaults(func=cmd_view)

    add_parser = subparsers.add_parser('add', help='Add a new inventory item.')
    add_parser.add_argument('--name', required=True)
    add_parser.add_argument('--brand')
    add_parser.add_argument('--barcode')
    add_parser.add_argument('--category')
    add_parser.add_argument('--price', type=float, required=True)
    add_parser.add_argument('--quantity', type=int, default=0)
    add_parser.set_defaults(func=cmd_add)

    update_parser = subparsers.add_parser('update', help='Update price and/or stock level for an item.')
    update_parser.add_argument('id', type=int)
    update_parser.add_argument('--price', type=float)
    update_parser.add_argument('--quantity', type=int)
    update_parser.set_defaults(func=cmd_update)

    delete_parser = subparsers.add_parser('delete', help='Delete an inventory item.')
    delete_parser.add_argument('id', type=int)
    delete_parser.set_defaults(func=cmd_delete)

    find_parser = subparsers.add_parser('find', help='Look up a product on OpenFoodFacts (does not modify inventory).')
    find_group = find_parser.add_mutually_exclusive_group(required=True)
    find_group.add_argument('--barcode')
    find_group.add_argument('--name')
    find_parser.set_defaults(func=cmd_find)

    import_parser = subparsers.add_parser('import', help='Fetch a product from OpenFoodFacts and add it to inventory.')
    import_group = import_parser.add_mutually_exclusive_group(required=True)
    import_group.add_argument('--barcode')
    import_group.add_argument('--name')
    import_parser.set_defaults(func=cmd_import)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except CLIError as error:
        print(f'Error: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
