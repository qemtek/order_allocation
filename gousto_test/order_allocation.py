import json
import pandas as pd
import numpy as np
from word2number import w2n

from gousto_test.utils.logging import get_logger
from gousto_test.utils.general import time_function

logger = get_logger()


class RecipeAllocator:
    def __init__(self, verbose=True):
        self.orders = None
        self.recipes = None
        self.portion_categories = None
        self.recipe_categories = None
        self.portion_categories_dict = dict()
        self.recipe_categories_dict = dict()
        self.box_types = list()
        self.acceptable_box_types = ["gourmet", "vegetarian"]
        self.verbose = verbose
        # Placeholder for excess stock after allocation
        self.excess_stock = None

    @staticmethod
    def load_json(file_path):
        """Load any json file, given a file path"""
        try:
            with open(file_path, "r") as f_in:
                return json.load(f_in)
        except Exception as e:
            logger.error(
                f"Failed to load orders file at {file_path}. Error: {e}"
            )

    def load_data(self, orders_dir="orders.json", recipes_dir="recipes.json"):
        """Load order and recipe data from a json file"""
        # Try to load the orders json
        self.orders = self.load_json(orders_dir)
        # Try to load the recipes json
        self.recipes = self.load_json(recipes_dir)
        # Scrape the distinct categories from the objects
        self.get_categories_from_json()
        # Check that vegetarian and gourmet exist as box_type categories
        for box_type in ["vegetarian", "gourmet"]:
            assert box_type in self.box_types, (
                f"Could not find {box_type} as a box_type category. The logic of this algorithm "
                "requires that vegetarian and gourmet exist as box types."
            )

    def get_orders(self):
        """Return the orders object"""
        return self.orders

    def get_recipes(self):
        """Return the recipes object"""
        return self.recipes

    def get_categories_from_json(self):
        """Get the distinct recipe categories and the distinct portion categories.
        Doing this ensures that if the number of recipes or portions a customer can specify
        changes, you wont need to change this code. We also create a mapping between words and numbers.

        DISCLAIMER: This code assumes that all orders have the same number of recipe options
        and that all recipes come in the same portion sizes.
        """
        if self.orders is not None and isinstance(self.orders, dict):
            self.box_types = list(self.orders.keys())
            self.recipe_categories = list(self.orders["gourmet"].keys())
            # Create a mapping between the recipe word and the recipe number
            for recipe in self.recipe_categories:
                try:
                    self.recipe_categories_dict[recipe] = w2n.word_to_num(
                        recipe.split("_")[0]
                    )
                except ValueError as e:
                    raise Exception(
                        f"Couldnt extract the number of recipes from the category. "
                        f"The logic of this algorithm assumes that category names are "
                        f"seperated by _ and the first word is the number. E.g. 'two_recipes. "
                        f"original error message: {e}"
                    )
            self.portion_categories = list(
                self.orders["gourmet"][self.recipe_categories[1]].keys()
            )
            # Create a mapping between the portion word and the portion number
            for portion in self.portion_categories:
                try:
                    self.portion_categories_dict[portion] = w2n.word_to_num(
                        portion.split("_")[0]
                    )
                except ValueError as e:
                    raise Exception(
                        f"Couldnt extract the number of portions from the category. "
                        f"The logic of this algorithm assumes that category names are "
                        f"seperated by _ and the first word is the number. E.g. 'two_portions. "
                        f"original error message: {e}"
                    )
        else:
            logger.error(
                "There was a problem obtaining categories from the data, has the data been loaded correctly?"
            )

    @staticmethod
    @time_function(logger=logger)
    def assign_order_group(
        *, df_stock, num_portions, num_recipes, num_orders, verbose=True
    ):
        """Work out how many orders we can fullfill, given a list of recipes and their stock
        numbers, along with the number of portions per order.
        """
        if verbose:
            logger.info(
                f"Fulfilling orders for a customer group. Number of portions: {num_portions}, "
                f"Number of recipes: {num_recipes}, Orders to fulfill: {num_orders}"
            )
            logger.info(f"Stock table: ")
            logger.info(df_stock)
        while num_orders != 0:
            # Work out which recipes can fulfill the stock requirement
            df_stock["sufficient_stock"] = df_stock["stock_count"].apply(
                lambda x: x > num_orders * num_portions
            )
            # Work out how many orders we can fulfull with each recipe
            df_stock["fulfillable_orders"] = df_stock["stock_count"].apply(
                lambda x: np.floor(x / num_portions)
            )
            # Work out how many recipes can fulfill more than 1 order
            df_stock["has_stock"] = df_stock["fulfillable_orders"].apply(
                lambda x: x > 0
            )

            # Test whether there are enough recipes with stock to fulfull the orders.
            # If there are not, we cannot ensure that customers will not recieve the same recipe twice.
            if sum(df_stock["has_stock"]) < num_recipes:
                logger.error(
                    "There are not enough recipes with sufficient stock to ensure that "
                    "customers do not get the same recipe twice, aborting."
                )
                return False

            # See how many recipes we can fulfill with the lowest stock recipe
            i = 0
            fulfillable_orders = 0
            while fulfillable_orders == 0:
                fulfillable_orders = df_stock.iloc[i, 3]
                if fulfillable_orders == 0:
                    # This is the index of the lowest stock recipe that can fulfill at least 1 order
                    i += 1
            # Make sure we do not fulfill more orders than we have
            fulfillable_orders = min(fulfillable_orders, num_orders)
            # Fulfill orders with the smallest recipe
            df_stock.iloc[i, 0] = (
                df_stock.iloc[i, 0] - fulfillable_orders * num_portions
            )
            # Fulfill the same number of orders with the largest recipes
            df_stock.iloc[-num_recipes + 1 :, 0] = (
                df_stock.iloc[-num_recipes + 1 :, 0]
                - fulfillable_orders * num_portions
            )
            # Re-sort the dataframe
            df_stock = df_stock.sort_values("stock_count")
            # Subtract the number of fulfilled orders from the stock requirement
            num_orders = num_orders - fulfillable_orders
        # Return the updated stock values for the recipes
        return df_stock[["stock_count", "box_type"]]

    @time_function(logger=logger)
    def assign_orders(self, *, box_type, excess_stock=None, verbose=True):
        """Assign recipes to customers for a given box_type, such that no customer
        recieves the same recipe twice. Start by fulfilling the largest orders and portion sizes first.
        """
        # Check that the correct inputs have been supplied
        assert (
            box_type in self.acceptable_box_types
        ), f"box_type can only be the following: {self.acceptable_box_types}"

        # Get the recipes for the chosen box_type
        recipes = {
            key: value
            for (key, value) in self.recipes.items()
            if value.get("box_type") == box_type
        }
        # Turn into a DataFrame so that its easier to work with
        df = pd.DataFrame.from_dict(recipes).transpose()
        # Add on the leftover stock, if any was supplied
        if excess_stock is not None:
            df = df.append(excess_stock[["stock_count", "box_type"]])
        # Ensure data types are correct
        df["stock_count"] = pd.to_numeric(df["stock_count"])
        # Get vegetarian orders
        orders = self.orders[box_type]
        # Start with 4 recipes, pair the recipe with the lowest stock with the recipes with the highest stock
        df = df.sort_values("stock_count")

        # Get the different portion and category options, and order them. We want to
        # fulfil the largest recipe/portion combinations first as it is the most
        # efficient way to fulfill orders.
        recipe_dict = self.recipe_categories_dict
        recipe_dict_values = list(recipe_dict.values())
        recipe_dict_values.sort(reverse=True)
        portion_dict = self.portion_categories_dict
        portion_dict_values = list(portion_dict.values())
        portion_dict_values.sort(reverse=True)
        # Loop through the recipe and portion categories and assign orders, starting with the largest of each.
        for recipe_num in recipe_dict_values:
            for portion_num in portion_dict_values:
                # Get the recipe and portion categories corresponding to the indexes
                recipe_category = list(recipe_dict.keys())[
                    list(recipe_dict.values()).index(recipe_num)
                ]
                portion_category = list(portion_dict.keys())[
                    list(portion_dict.values()).index(portion_num)
                ]
                # Get the orders to fulfill for the recipe and portion combination
                try:
                    orders_to_fulfill = orders[recipe_category][
                        portion_category
                    ]
                except KeyError as e:
                    raise Exception(
                        f"recipe: {recipe_category}, portion: {portion_category} does not "
                        f"exist for the {box_type} customer group. This code assumes that "
                        f"all customer groups have the same categories. Please change the "
                        f"way categories are scraped if this is no longer true. Error message: {e}"
                    )
                df = self.assign_order_group(
                    df_stock=df,
                    num_portions=portion_num,
                    num_recipes=recipe_num,
                    num_orders=orders_to_fulfill,
                    verbose=verbose,
                )
                if df is False:
                    return {"success": False, "excess_stock": None}
        logger.info(
            f"{box_type} orders allocated successfully. Returning leftover stock"
        )
        if verbose:
            logger.info(df)
        return {"success": True, "excess_stock": df}

    @time_function(logger=logger)
    def run(self, *, orders_dir, recipes_dir):
        """Load json files containing recipes and orders and attempt to allocate them. Return True if
        allocation within the constraints was successful, otherwise return False. Allocate the vegetarian
        orders first as vegeratians have a smaller pool of options available to them.
        """
        self.load_data(orders_dir=orders_dir, recipes_dir=recipes_dir)
        # Attempt to allocate all of the vegetarian orders such that no customer receives the same recipe twice
        veg_result = self.assign_orders(box_type="vegetarian")
        if veg_result["success"] is False:
            return False
        # Attempt to allocate all of the gourmet orders such that no customer receives the same recipe twice
        gourmet_result = self.assign_orders(
            box_type="gourmet", excess_stock=veg_result["excess_stock"]
        )
        # Return the exit status of the gourmet recipe allocation, which is true if all contstraints have been met
        if gourmet_result["success"]:
            logger.info(
                "Allocation successful! Returning true, excess stock can be found in self.excess_stock"
            )
            self.excess_stock = gourmet_result["excess_stock"]
            return True
        else:
            return False


if __name__ == "__main__":
    ra = RecipeAllocator()
    ra.run()
