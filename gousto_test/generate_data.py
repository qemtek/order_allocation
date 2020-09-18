import random
import json

from gousto_test.utils.logging import get_logger

logger = get_logger()


class DataGenerator:
    """Class for generating sample data to test the stock allocation algorithm created in this test"""

    def __init__(
        self,
        max_recipes=40,
        min_recipes=20,
        max_stock=30000,
        min_stock=10000,
        min_orders=1000,
        max_orders=5000,
        order_groups=None,
        portion_options=None,
        recipe_options=None,
    ):
        # Set limits on the number of recipes
        self.max_recipes = max_recipes
        self.min_recipes = min_recipes
        # Set limits on recipe stock
        self.max_stock = max_stock
        self.min_stock = min_stock
        # Set limits on customer orders
        self.max_orders = max_orders
        self.min_orders = min_orders
        # Other parameters for generating order data
        self.vegetarian_recipe_portion = 0.26666666666666666  # Veg fraction taken from the data supplied by Gousto
        self.order_groups = (
            order_groups
            if order_groups is not None
            else ["vegetarian", "gourmet"]
        )
        self.portion_options = (
            portion_options
            if portion_options is not None
            else ["two_portions", "four_portions"]
        )
        self.recipe_options = (
            recipe_options
            if recipe_options is not None
            else ["two_recipes", "three_recipes", "four_recipes"]
        )

    @staticmethod
    def generate_random_number(
        min, max, distribution="uniform", round_output=True
    ):
        """Generate a random number from a distribution"""
        if distribution == "uniform":
            output = random.uniform(min, max)
            return output if not round_output else round(output)
        else:
            raise NotImplementedError(
                "Only uniform number generation has been implemented so far"
            )

    @staticmethod
    def save_json(object, save_dir):
        try:
            with open(save_dir, "w") as f_out:
                json.dump(object, fp=f_out)
        except Exception as e:
            logger.error(f"Saving json failed, error: {e}")

    def generate_recipes(self, save_dir=None):
        """Generate recipes and stock amounts based on the parameters set in __init__()"""
        n_recipes = self.generate_random_number(
            self.min_recipes, self.max_recipes
        )
        recipe_dict = dict()
        for i in range(1, n_recipes + 1):
            recipe_dict[f"recipe_{i}"] = {
                "stock_count": self.generate_random_number(
                    self.min_stock, self.max_stock
                ),
                "box_type": "vegetarian"
                if random.uniform(0, 1) < self.vegetarian_recipe_portion
                else "gourmet",
            }
        if save_dir is None:
            return recipe_dict
        else:
            self.save_json(recipe_dict, save_dir)

    def generate_orders(self, save_dir=None):
        """Generate customer orders based on the parameters set in __init__()"""
        order_dict = {}
        for group in self.order_groups:
            order_dict[group] = {}
            for recipe in self.recipe_options:
                order_dict[group][recipe] = {}
                for portion in self.portion_options:
                    order_dict[group][recipe][
                        portion
                    ] = self.generate_random_number(
                        self.min_orders, self.max_orders
                    )
        if save_dir is None:
            return order_dict
        else:
            self.save_json(order_dict, save_dir)


if __name__ == "__main__":
    generator = DataGenerator()
    recipes = generator.generate_recipes("recipes.json")
    orders = generator.generate_orders("orders.json")
