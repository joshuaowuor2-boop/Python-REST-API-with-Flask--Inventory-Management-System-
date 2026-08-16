#!/usr/bin/env python3

import pytest

import storage


def pytest_itemcollected(item):
    par = item.parent.obj
    node = item.obj
    pref = par.__doc__.strip() if par.__doc__ else par.__class__.__name__
    suf = node.__doc__.strip() if node.__doc__ else node.__name__
    if pref or suf:
        item._nodeid = ' '.join((pref, suf))


@pytest.fixture(autouse=True)
def reset_storage():
    '''Reset the in-memory inventory list before every test so tests stay isolated.'''
    storage.reset()
    yield
    storage.reset()


@pytest.fixture
def client():
    from app import app
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client
