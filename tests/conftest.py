import json
import pytest


@pytest.fixture
def orders_json():
    with open("tests/orders.json", "r") as f_in:
        yield json.load(f_in)


@pytest.fixture
def recipes_json():
    with open("tests/recipes.json", "r") as f_in:
        yield json.load(f_in)
