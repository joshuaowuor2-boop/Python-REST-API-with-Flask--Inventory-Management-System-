#!/usr/bin/env python3
'''Client for the OpenFoodFacts API, used to enrich inventory items.'''

import requests

BASE_URL = 'https://world.openfoodfacts.org'
TIMEOUT = 10
# OpenFoodFacts blocks requests using the default python-requests User-Agent.
HEADERS = {'User-Agent': 'InventoryManagementSystem/1.0 (contact@example.com)'}


class ExternalAPIError(Exception):
    '''Raised when the OpenFoodFacts API can't be reached or returns bad data.'''


def normalize_product(raw_product, barcode=None):
    '''Map an OpenFoodFacts product dict onto our inventory schema.'''
    return {
        'product_name': raw_product.get('product_name') or 'Unknown Product',
        'brands': raw_product.get('brands'),
        'barcode': raw_product.get('code') or barcode,
        'category': (raw_product.get('categories') or '').split(',')[0].strip() or None,
        'ingredients_text': raw_product.get('ingredients_text'),
        'image_url': raw_product.get('image_url'),
        'source': 'openfoodfacts',
    }


def fetch_by_barcode(barcode):
    '''Look up a single product by barcode. Returns a normalized dict, or None if not found.'''
    try:
        response = requests.get(
            f'{BASE_URL}/api/v2/product/{barcode}.json', headers=HEADERS, timeout=TIMEOUT
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as error:
        raise ExternalAPIError(f'Could not reach OpenFoodFacts: {error}') from error

    data = response.json()
    if data.get('status') != 1:
        return None
    return normalize_product(data.get('product', {}), barcode=barcode)


def search_by_name(name, limit=5):
    '''Search products by name. Returns a list of normalized dicts (possibly empty).'''
    try:
        response = requests.get(
            f'{BASE_URL}/api/v2/search',
            params={'search_terms': name, 'page_size': limit},
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as error:
        raise ExternalAPIError(f'Could not reach OpenFoodFacts: {error}') from error

    data = response.json()
    products = data.get('products', [])[:limit]
    return [normalize_product(product) for product in products]
