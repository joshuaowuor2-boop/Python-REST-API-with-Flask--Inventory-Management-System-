#!/usr/bin/env python3
'''Flask REST API for the retail Inventory Management System.'''

from flask import Flask, jsonify, request

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


if __name__ == '__main__':
    app.run(port=5000, debug=True)
