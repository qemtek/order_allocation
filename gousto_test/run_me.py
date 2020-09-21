"""Here I have added a script that continuously generates data and solves it using the allocator
"""
from gousto_test.generate_data import DataGenerator
from gousto_test.order_allocation import RecipeAllocator

# Uncomment and run this to generate new data
# generator = DataGenerator()
# generator.generate_recipes(save_dir="recipes.json")
# generator.generate_orders(save_dir="orders.json")

allocator = RecipeAllocator()
leftover_stock = allocator.run(
    orders_dir="orders_original.json", recipes_dir="recipes_original.json"
)
