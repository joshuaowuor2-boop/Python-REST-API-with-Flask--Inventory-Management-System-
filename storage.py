#!/usr/bin/env python3
'''In-memory inventory "database" and CRUD helpers.

Mimics a simple table: a list of dicts, each shaped roughly like an
OpenFoodFacts product plus the retail fields an inventory system needs
(price, quantity_in_stock, source).
'''


def _seed_data():
    return [
        {
            'id': 1,
            'product_name': 'Organic Almond Milk',
            'brands': 'Silk',
            'barcode': '0025293001156',
            'category': 'Dairy Alternatives',
            'ingredients_text': 'Filtered water, almonds, cane sugar, sea salt, ...',
            'image_url': None,
            'price': 4.99,
            'quantity_in_stock': 25,
            'source': 'manual',
        },
        {
            'id': 2,
            'product_name': 'Extra Virgin Olive Oil',
            'brands': "Bertolli",
            'barcode': '0064944001010',
            'category': 'Cooking Oils',
            'ingredients_text': '100% Extra Virgin Olive Oil',
            'image_url': None,
            'price': 8.49,
            'quantity_in_stock': 40,
            'source': 'manual',
        },
        {
            'id': 3,
            'product_name': 'Sourdough Bread',
            'brands': 'La Brea Bakery',
            'barcode': '0071140457005',
            'category': 'Bakery',
            'ingredients_text': 'Wheat flour, water, salt, sourdough culture',
            'image_url': None,
            'price': 5.29,
            'quantity_in_stock': 15,
            'source': 'manual',
        },
        {
            'id': 4,
            'product_name': 'Sparkling Water, Lime',
            'brands': 'LaCroix',
            'barcode': '0017586001108',
            'category': 'Beverages',
            'ingredients_text': 'Carbonated water, natural lime flavor',
            'image_url': None,
            'price': 3.99,
            'quantity_in_stock': 60,
            'source': 'manual',
        },
    ]


inventory = _seed_data()


def reset():
    '''Restore the inventory list to its original seed data. Used by tests.'''
    global inventory
    inventory = _seed_data()
    return inventory


def get_all():
    return inventory


def get_by_id(item_id):
    return next((item for item in inventory if item['id'] == item_id), None)


def _next_id():
    return max((item['id'] for item in inventory), default=0) + 1


def create(data):
    item = {
        'id': _next_id(),
        'product_name': data.get('product_name'),
        'brands': data.get('brands'),
        'barcode': data.get('barcode'),
        'category': data.get('category'),
        'ingredients_text': data.get('ingredients_text'),
        'image_url': data.get('image_url'),
        'price': data.get('price'),
        'quantity_in_stock': data.get('quantity_in_stock', 0),
        'source': data.get('source', 'manual'),
    }
    inventory.append(item)
    return item


def update(item_id, data):
    item = get_by_id(item_id)
    if item is None:
        return None
    item.update({key: value for key, value in data.items() if key in item})
    return item


def delete(item_id):
    item = get_by_id(item_id)
    if item is None:
        return False
    inventory.remove(item)
    return True
