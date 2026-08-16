#!/usr/bin/env python3
'''Flask REST API for the retail Inventory Management System.'''

from flask import Flask, jsonify, request

import external_api
import storage

app = Flask(__name__)

REQUIRED_FIELDS = ('product_name', 'price')


@app.route('/')
def index():
    return jsonify({'message': 'Inventory Management System API'})


@app.route('/inventory', methods=['GET'])
def get_inventory():
    return jsonify(storage.get_all()), 200


@app.route('/inventory/<int:item_id>', methods=['GET'])
def get_inventory_item(item_id):
    item = storage.get_by_id(item_id)
    if item is None:
        return jsonify({'error': f'No inventory item found with id {item_id}'}), 404
    return jsonify(item), 200


@app.route('/inventory', methods=['POST'])
def create_inventory_item():
    data = request.get_json(silent=True) or {}
    missing = [field for field in REQUIRED_FIELDS if not data.get(field)]
    if missing:
        return jsonify({'error': f'Missing required field(s): {", ".join(missing)}'}), 400
    item = storage.create(data)
    return jsonify(item), 201


@app.route('/inventory/<int:item_id>', methods=['PATCH'])
def update_inventory_item(item_id):
    data = request.get_json(silent=True) or {}
    item = storage.update(item_id, data)
    if item is None:
        return jsonify({'error': f'No inventory item found with id {item_id}'}), 404
    return jsonify(item), 200


@app.route('/inventory/<int:item_id>', methods=['DELETE'])
def delete_inventory_item(item_id):
    deleted = storage.delete(item_id)
    if not deleted:
        return jsonify({'error': f'No inventory item found with id {item_id}'}), 404
    return '', 204


@app.route('/inventory/lookup', methods=['GET'])
def lookup_external_product():
    '''Query OpenFoodFacts by barcode or name without touching inventory storage.'''
    barcode = request.args.get('barcode')
    name = request.args.get('name')
    if not barcode and not name:
        return jsonify({'error': 'Provide a "barcode" or "name" query parameter'}), 400

    try:
        if barcode:
            result = external_api.fetch_by_barcode(barcode)
            if result is None:
                return jsonify({'error': f'No product found for barcode {barcode}'}), 404
            return jsonify(result), 200
        results = external_api.search_by_name(name)
        return jsonify(results), 200
    except external_api.ExternalAPIError as error:
        return jsonify({'error': str(error)}), 502


@app.route('/inventory/import', methods=['POST'])
def import_external_product():
    '''Fetch a product from OpenFoodFacts and add it to the inventory array.'''
    data = request.get_json(silent=True) or {}
    barcode = data.get('barcode')
    name = data.get('name')
    if not barcode and not name:
        return jsonify({'error': 'Provide a "barcode" or "name" field'}), 400

    try:
        if barcode:
            product = external_api.fetch_by_barcode(barcode)
            if product is None:
                return jsonify({'error': f'No product found for barcode {barcode}'}), 404
        else:
            matches = external_api.search_by_name(name, limit=1)
            if not matches:
                return jsonify({'error': f'No product found for name "{name}"'}), 404
            product = matches[0]
    except external_api.ExternalAPIError as error:
        return jsonify({'error': str(error)}), 502

    product.setdefault('price', 0)
    product.setdefault('quantity_in_stock', 0)
    item = storage.create(product)
    return jsonify(item), 201


if __name__ == '__main__':
    app.run(port=5000, debug=True)
