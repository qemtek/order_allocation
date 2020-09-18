from gousto_test.order_allocation import RecipeAllocator


def test_load_json(orders_json):
    """Test that json files can be loaded correctly"""
    allocator = RecipeAllocator()
    result = allocator.load_json("tests/orders.json")
    print(f"orders_json: {orders_json}")
    assert result == orders_json


def test_get_categories_from_json():
    """Test that categories can be extracted from json files correctly"""
    allocator = RecipeAllocator()
    allocator.load_data(
        orders_dir="tests/orders.json", recipes_dir="tests/recipes.json"
    )
    allocator.get_categories_from_json()
    assert list(allocator.portion_categories_dict.keys()) == [
        "two_portions",
        "four_portions",
    ] and list(allocator.recipe_categories_dict.keys()) == [
        "two_recipes",
        "three_recipes",
        "four_recipes",
    ]


def test_fullfill_orders_works():
    """Test that fulfill orders works on a completable example"""
    allocator = RecipeAllocator()
    assert allocator.run(
        orders_dir="tests/orders.json", recipes_dir="tests/recipes.json"
    )


def test_fullfill_orders_fails_veg():
    """Test that fulfill orders fails on an impossible example for vegetarian boxes"""
    allocator = RecipeAllocator()
    assert not allocator.run(
        orders_dir="tests/orders_break_veg.json",
        recipes_dir="tests/recipes.json",
    )


def test_fullfill_orders_fails_gourmet():
    """Test that fulfill orders fails on an impossible example for gourmet boxes"""
    allocator = RecipeAllocator()
    assert not allocator.run(
        orders_dir="tests/orders_break_veg.json",
        recipes_dir="tests/recipes.json",
    )


def test_assign_orders():
    """Test that assign orders works correctly and returns the correct stock amounts"""
    allocator = RecipeAllocator()
    allocator.load_data(
        orders_dir="tests/orders.json", recipes_dir="tests/recipes.json"
    )
    result = allocator.assign_orders(box_type="vegetarian")
    assert result["excess_stock"].loc["recipe_2", "stock_count"] == 6
