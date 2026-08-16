from unittest.mock import Mock, patch

import pytest
import requests

import cli


def _mock_response(status_code=200, json_data=None):
    response = Mock()
    response.status_code = status_code
    response.json.return_value = json_data if json_data is not None else {}
    response.text = str(json_data)
    return response


class TestArgParsing:
    '''cli.build_parser'''

    def test_requires_a_command(self):
        '''exits with an error when no subcommand is given.'''
        with pytest.raises(SystemExit):
            cli.build_parser().parse_args([])

    def test_add_rejects_non_numeric_price(self):
        '''exits with an error when --price is not a number.'''
        with pytest.raises(SystemExit):
            cli.build_parser().parse_args(['add', '--name', 'Widget', '--price', 'not-a-number'])

    def test_find_requires_barcode_or_name(self):
        '''exits with an error when neither --barcode nor --name is given.'''
        with pytest.raises(SystemExit):
            cli.build_parser().parse_args(['find'])


class TestCommands:
    '''cli command functions, HTTP layer mocked'''

    @patch('cli.requests.request')
    def test_list_prints_each_item(self, mock_request, capsys):
        '''"list" prints every inventory item.'''
        mock_request.return_value = _mock_response(200, [
            {'id': 1, 'product_name': 'Almond Milk', 'brands': 'Silk', 'price': 4.99, 'quantity_in_stock': 25, 'barcode': '123'},
        ])
        args = cli.build_parser().parse_args(['list'])
        args.func(args)
        out = capsys.readouterr().out
        assert 'Almond Milk' in out
        mock_request.assert_called_once_with('GET', 'http://localhost:5000/inventory', timeout=10)

    @patch('cli.requests.request')
    def test_list_prints_message_when_empty(self, mock_request, capsys):
        '''"list" prints a friendly message when inventory is empty.'''
        mock_request.return_value = _mock_response(200, [])
        args = cli.build_parser().parse_args(['list'])
        args.func(args)
        assert 'empty' in capsys.readouterr().out.lower()

    @patch('cli.requests.request')
    def test_view_prints_item(self, mock_request, capsys):
        '''"view <id>" prints the requested item.'''
        mock_request.return_value = _mock_response(200, {'id': 2, 'product_name': 'Olive Oil', 'brands': 'Bertolli', 'price': 8.49, 'quantity_in_stock': 40, 'barcode': '456'})
        args = cli.build_parser().parse_args(['view', '2'])
        args.func(args)
        assert 'Olive Oil' in capsys.readouterr().out

    @patch('cli.requests.request')
    def test_view_raises_cli_error_on_404(self, mock_request):
        '''"view <id>" raises CLIError when the item doesn't exist.'''
        mock_request.return_value = _mock_response(404, {'error': 'No inventory item found with id 9999'})
        args = cli.build_parser().parse_args(['view', '9999'])
        with pytest.raises(cli.CLIError):
            args.func(args)

    @patch('cli.requests.request')
    def test_add_posts_expected_payload(self, mock_request, capsys):
        '''"add" POSTs the provided fields and prints the created item.'''
        mock_request.return_value = _mock_response(201, {'id': 5, 'product_name': 'Widget', 'brands': None, 'price': 1.5, 'quantity_in_stock': 3, 'barcode': None})
        args = cli.build_parser().parse_args(['add', '--name', 'Widget', '--price', '1.5', '--quantity', '3'])
        args.func(args)
        method, url = mock_request.call_args.args
        assert method == 'POST'
        assert url == 'http://localhost:5000/inventory'
        assert mock_request.call_args.kwargs['json']['product_name'] == 'Widget'
        assert 'Widget' in capsys.readouterr().out

    @patch('cli.requests.request')
    def test_update_sends_only_provided_fields(self, mock_request):
        '''"update <id>" only includes --price/--quantity that were actually passed.'''
        mock_request.return_value = _mock_response(200, {'id': 1, 'product_name': 'X', 'price': 9.99, 'quantity_in_stock': 1, 'barcode': None, 'brands': None})
        args = cli.build_parser().parse_args(['update', '1', '--price', '9.99'])
        args.func(args)
        assert mock_request.call_args.kwargs['json'] == {'price': 9.99}

    def test_update_with_no_fields_raises_cli_error(self):
        '''"update <id>" with neither --price nor --quantity raises CLIError.'''
        args = cli.build_parser().parse_args(['update', '1'])
        with pytest.raises(cli.CLIError):
            args.func(args)

    @patch('cli.requests.request')
    def test_delete_prints_confirmation(self, mock_request, capsys):
        '''"delete <id>" prints a confirmation message.'''
        mock_request.return_value = _mock_response(204)
        args = cli.build_parser().parse_args(['delete', '3'])
        args.func(args)
        assert 'Deleted item 3' in capsys.readouterr().out

    @patch('cli.requests.request')
    def test_find_by_barcode_queries_lookup_route(self, mock_request, capsys):
        '''"find --barcode" hits /inventory/lookup with the barcode param.'''
        mock_request.return_value = _mock_response(200, {'product_name': 'Almond Milk', 'brands': 'Silk', 'barcode': '123'})
        args = cli.build_parser().parse_args(['find', '--barcode', '123'])
        args.func(args)
        assert mock_request.call_args.kwargs['params'] == {'barcode': '123'}
        assert 'Almond Milk' in capsys.readouterr().out

    @patch('cli.requests.request')
    def test_import_by_name_posts_to_import_route(self, mock_request, capsys):
        '''"import --name" POSTs to /inventory/import and prints the created item.'''
        mock_request.return_value = _mock_response(201, {'id': 9, 'product_name': 'Almond Milk', 'brands': 'Silk', 'price': 0, 'quantity_in_stock': 0, 'barcode': '123'})
        args = cli.build_parser().parse_args(['import', '--name', 'almond milk'])
        args.func(args)
        method, url = mock_request.call_args.args
        assert method == 'POST'
        assert url == 'http://localhost:5000/inventory/import'
        assert mock_request.call_args.kwargs['json'] == {'name': 'almond milk'}
        assert 'Imported' in capsys.readouterr().out

    @patch('cli.requests.request')
    def test_network_error_raises_cli_error(self, mock_request):
        '''A network failure (server not running) raises a friendly CLIError.'''
        mock_request.side_effect = requests.exceptions.ConnectionError('refused')
        args = cli.build_parser().parse_args(['list'])
        with pytest.raises(cli.CLIError):
            args.func(args)


class TestMain:
    '''cli.main'''

    @patch('cli.requests.request')
    def test_main_returns_nonzero_and_prints_to_stderr_on_error(self, mock_request, capsys):
        '''main() catches CLIError, prints to stderr, and returns exit code 1.'''
        mock_request.side_effect = requests.exceptions.ConnectionError('refused')
        exit_code = cli.main(['list'])
        assert exit_code == 1
        assert 'Error' in capsys.readouterr().err

    @patch('cli.requests.request')
    def test_main_returns_zero_on_success(self, mock_request):
        '''main() returns 0 when the command succeeds.'''
        mock_request.return_value = _mock_response(200, [])
        assert cli.main(['list']) == 0
