from unittest.mock import Mock, patch

import pytest
import requests

import external_api

OFF_FOUND_RESPONSE = {
    'status': 1,
    'product': {
        'product_name': 'Organic Almond Milk',
        'brands': 'Silk',
        'code': '0025293001156',
        'categories': 'Beverages, Plant-based milks',
        'ingredients_text': 'Filtered water, almonds, cane sugar, ...',
        'image_url': 'https://images.openfoodfacts.org/almond-milk.jpg',
    },
}

OFF_NOT_FOUND_RESPONSE = {'status': 0}

OFF_SEARCH_RESPONSE = {
    'products': [
        {'product_name': 'Almond Milk A', 'brands': 'Silk', 'code': '111'},
        {'product_name': 'Almond Milk B', 'brands': 'Califia', 'code': '222'},
    ]
}


def _mock_response(json_data, raise_for_status=None):
    response = Mock()
    response.json.return_value = json_data
    response.raise_for_status.side_effect = raise_for_status
    return response


class TestFetchByBarcode:
    '''external_api.fetch_by_barcode'''

    @patch('external_api.requests.get')
    def test_returns_normalized_product_when_found(self, mock_get):
        '''returns a normalized dict when OpenFoodFacts finds a match.'''
        mock_get.return_value = _mock_response(OFF_FOUND_RESPONSE)
        result = external_api.fetch_by_barcode('0025293001156')
        assert result['product_name'] == 'Organic Almond Milk'
        assert result['brands'] == 'Silk'
        assert result['barcode'] == '0025293001156'
        assert result['category'] == 'Beverages'
        assert result['source'] == 'openfoodfacts'

    @patch('external_api.requests.get')
    def test_returns_none_when_not_found(self, mock_get):
        '''returns None when OpenFoodFacts has no match (status 0).'''
        mock_get.return_value = _mock_response(OFF_NOT_FOUND_RESPONSE)
        assert external_api.fetch_by_barcode('0000000000000') is None

    @patch('external_api.requests.get')
    def test_raises_external_api_error_on_network_failure(self, mock_get):
        '''raises ExternalAPIError when the request fails.'''
        mock_get.side_effect = requests.exceptions.ConnectionError('boom')
        with pytest.raises(external_api.ExternalAPIError):
            external_api.fetch_by_barcode('123')


class TestSearchByName:
    '''external_api.search_by_name'''

    @patch('external_api.requests.get')
    def test_returns_normalized_list(self, mock_get):
        '''returns a list of normalized products.'''
        mock_get.return_value = _mock_response(OFF_SEARCH_RESPONSE)
        results = external_api.search_by_name('almond milk')
        assert len(results) == 2
        assert results[0]['product_name'] == 'Almond Milk A'
        assert results[1]['barcode'] == '222'

    @patch('external_api.requests.get')
    def test_returns_empty_list_when_no_matches(self, mock_get):
        '''returns an empty list when there are no products.'''
        mock_get.return_value = _mock_response({'products': []})
        assert external_api.search_by_name('doesnotexist') == []

    @patch('external_api.requests.get')
    def test_raises_external_api_error_on_network_failure(self, mock_get):
        '''raises ExternalAPIError when the request fails.'''
        mock_get.side_effect = requests.exceptions.Timeout('timed out')
        with pytest.raises(external_api.ExternalAPIError):
            external_api.search_by_name('almond milk')
