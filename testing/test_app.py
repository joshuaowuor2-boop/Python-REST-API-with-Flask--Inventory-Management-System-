import storage


class TestInventoryCRUD:
    '''Inventory CRUD routes in app.py'''

    def test_get_inventory_returns_all_items(self, client):
        '''GET /inventory returns every seeded item.'''
        response = client.get('/inventory')
        assert response.status_code == 200
        assert len(response.get_json()) == len(storage.get_all())

    def test_get_inventory_item_returns_single_item(self, client):
        '''GET /inventory/<id> returns the matching item.'''
        response = client.get('/inventory/1')
        assert response.status_code == 200
        assert response.get_json()['id'] == 1

    def test_get_inventory_item_404_when_missing(self, client):
        '''GET /inventory/<id> 404s for an id that does not exist.'''
        response = client.get('/inventory/9999')
        assert response.status_code == 404
        assert 'error' in response.get_json()

    def test_post_inventory_creates_item(self, client):
        '''POST /inventory adds a new item to the inventory array.'''
        payload = {'product_name': 'Peanut Butter', 'brands': 'Jif', 'price': 3.49, 'quantity_in_stock': 10}
        response = client.post('/inventory', json=payload)
        assert response.status_code == 201
        created = response.get_json()
        assert created['product_name'] == 'Peanut Butter'
        assert created['id'] is not None
        assert len(storage.get_all()) == 5

    def test_post_inventory_400_when_missing_required_fields(self, client):
        '''POST /inventory 400s when product_name or price is missing.'''
        response = client.post('/inventory', json={'brands': 'No Name'})
        assert response.status_code == 400
        assert 'error' in response.get_json()

    def test_patch_inventory_item_updates_fields(self, client):
        '''PATCH /inventory/<id> updates only the provided fields.'''
        response = client.patch('/inventory/2', json={'price': 9.99, 'quantity_in_stock': 5})
        assert response.status_code == 200
        updated = response.get_json()
        assert updated['price'] == 9.99
        assert updated['quantity_in_stock'] == 5
        assert updated['product_name'] == 'Extra Virgin Olive Oil'

    def test_patch_inventory_item_404_when_missing(self, client):
        '''PATCH /inventory/<id> 404s for an id that does not exist.'''
        response = client.patch('/inventory/9999', json={'price': 1.00})
        assert response.status_code == 404

    def test_delete_inventory_item_removes_item(self, client):
        '''DELETE /inventory/<id> removes the item from the inventory array.'''
        response = client.delete('/inventory/3')
        assert response.status_code == 204
        assert storage.get_by_id(3) is None

    def test_delete_inventory_item_404_when_missing(self, client):
        '''DELETE /inventory/<id> 404s for an id that does not exist.'''
        response = client.delete('/inventory/9999')
        assert response.status_code == 404
