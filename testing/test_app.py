from unittest.mock import patch

import external_api
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


class TestInventoryExternalLookup:
    '''External API routes in app.py'''

    def test_lookup_requires_barcode_or_name(self, client):
        '''GET /inventory/lookup 400s with no query params.'''
        response = client.get('/inventory/lookup')
        assert response.status_code == 400

    @patch('app.external_api.fetch_by_barcode')
    def test_lookup_by_barcode_returns_product(self, mock_fetch, client):
        '''GET /inventory/lookup?barcode= returns the normalized product.'''
        mock_fetch.return_value = {'product_name': 'Almond Milk', 'barcode': '123', 'source': 'openfoodfacts'}
        response = client.get('/inventory/lookup?barcode=123')
        assert response.status_code == 200
        assert response.get_json()['product_name'] == 'Almond Milk'
        mock_fetch.assert_called_once_with('123')

    @patch('app.external_api.fetch_by_barcode')
    def test_lookup_by_barcode_404_when_not_found(self, mock_fetch, client):
        '''GET /inventory/lookup?barcode= 404s when OpenFoodFacts has no match.'''
        mock_fetch.return_value = None
        response = client.get('/inventory/lookup?barcode=000')
        assert response.status_code == 404

    @patch('app.external_api.search_by_name')
    def test_lookup_by_name_returns_results(self, mock_search, client):
        '''GET /inventory/lookup?name= returns a list of matches.'''
        mock_search.return_value = [{'product_name': 'Almond Milk', 'source': 'openfoodfacts'}]
        response = client.get('/inventory/lookup?name=almond')
        assert response.status_code == 200
        assert response.get_json() == mock_search.return_value

    @patch('app.external_api.fetch_by_barcode')
    def test_lookup_502_on_external_api_error(self, mock_fetch, client):
        '''GET /inventory/lookup returns 502 when OpenFoodFacts is unreachable.'''
        mock_fetch.side_effect = external_api.ExternalAPIError('down')
        response = client.get('/inventory/lookup?barcode=123')
        assert response.status_code == 502


class TestInventoryImport:
    '''POST /inventory/import in app.py'''

    def test_import_requires_barcode_or_name(self, client):
        '''POST /inventory/import 400s with no body fields.'''
        response = client.post('/inventory/import', json={})
        assert response.status_code == 400

    @patch('app.external_api.fetch_by_barcode')
    def test_import_by_barcode_adds_item_to_inventory(self, mock_fetch, client):
        '''POST /inventory/import with a barcode fetches and appends a new item.'''
        mock_fetch.return_value = {'product_name': 'Almond Milk', 'barcode': '123', 'source': 'openfoodfacts'}
        before = len(storage.get_all())
        response = client.post('/inventory/import', json={'barcode': '123'})
        assert response.status_code == 201
        created = response.get_json()
        assert created['product_name'] == 'Almond Milk'
        assert created['id'] is not None
        assert len(storage.get_all()) == before + 1

    @patch('app.external_api.fetch_by_barcode')
    def test_import_by_barcode_404_when_not_found(self, mock_fetch, client):
        '''POST /inventory/import 404s when OpenFoodFacts has no match, and inventory is unchanged.'''
        mock_fetch.return_value = None
        before = len(storage.get_all())
        response = client.post('/inventory/import', json={'barcode': '000'})
        assert response.status_code == 404
        assert len(storage.get_all()) == before

    @patch('app.external_api.search_by_name')
    def test_import_by_name_adds_first_match(self, mock_search, client):
        '''POST /inventory/import with a name imports the first search match.'''
        mock_search.return_value = [{'product_name': 'Almond Milk', 'source': 'openfoodfacts'}]
        response = client.post('/inventory/import', json={'name': 'almond'})
        assert response.status_code == 201
        assert response.get_json()['product_name'] == 'Almond Milk'
