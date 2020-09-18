"""Here I have added a script that continuously generates data and solves it using the allocator
"""
from gousto_test.generate_data import DataGenerator
from gousto_test.order_allocation import RecipeAllocator

generator = DataGenerator()
generator.generate_recipes("recipes.json")
generator.generate_orders("orders.json")

allocator = RecipeAllocator()
leftover_stock = allocator.run(
    orders_dir="orders.json", recipes_dir="recipes.json"
)
