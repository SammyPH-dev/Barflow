from datetime import date, timedelta
from logging import raiseExceptions

from .schemas import (Recommendations, ExpiringDrink, PopularDrink, RecipeSalesCount)
from src.services.recommender.inventory_client import get_inventory_stock
from .schemas import Stock, Recipe

sample_recipes = [{  # Simulate a recipe-service lookup until its endpoint is ready.
    "recipe_id": 1,
    "name": "Mojito",
    "ingredient_ids": [
        {"ingredient_id": 1, "quantity": "50.000", "unit": "ml"},
        {"ingredient_id": 23, "quantity": "5.000", "unit": "g"},
        {"ingredient_id": 11, "quantity": "25.000", "unit": "ml"},
        {"ingredient_id": 10, "quantity": "15.000", "unit": "ml"},
        {"ingredient_id": 16, "quantity": "100.000", "unit": "ml"},
    ]
}, {
    "recipe_id": 2,
    "name": "Margarita",
    "ingredient_ids": [
        {"ingredient_id": 5, "quantity": "50.000", "unit": "ml"},
        {"ingredient_id": 6, "quantity": "25.000", "unit": "ml"},
        {"ingredient_id": 11, "quantity": "25.000", "unit": "ml"},
    ],
}, {
    "recipe_id": 3,
    "name": "Lait à la menthe et à la lime",
    "ingredient_ids": [
        {"ingredient_id": 11, "quantity": "15.000", "unit": "ml"},
        {"ingredient_id": 14, "quantity": "200.000", "unit": "ml"},
        {"ingredient_id": 23, "quantity": "5.000", "unit": "g"},
    ],
}, {
    "recipe_id": 4,
    "name": "Vodka canneberge",
    "ingredient_ids": [
        {"ingredient_id": 2, "quantity": "50.000", "unit": "ml"},
        {"ingredient_id": 13, "quantity": "150.000", "unit": "ml"},
    ],
},{
    "recipe_id": 5,
    "name": "Breuvage test — expiration demain",
    "ingredient_ids": [
        {"ingredient_id": 26, "quantity": "100.000", "unit": "ml"},
    ],
},
]

async def get_recipe_sales_counts() -> list[RecipeSalesCount]:
    """Simulate sales totals until the order-service endpoint is ready."""

    return [
        RecipeSalesCount(recipe_id=1, quantity_ordered=28),
        RecipeSalesCount(recipe_id=2, quantity_ordered=45),
        RecipeSalesCount(recipe_id=3, quantity_ordered=12),
        RecipeSalesCount(recipe_id=4, quantity_ordered=20),
    ]


async def get_recommendations() -> Recommendations:
    """Calculate both lists using one inventory response."""

    stocks = await get_inventory_stock(
        "http://localhost:8002", 1, "employee"
    )

    expiring_drinks = await get_expiring_recipe_recommendations(stocks)
    popular_drinks = await get_popular_drink_recommendations(stocks)

    return Recommendations(
        expiring_drinks=expiring_drinks,
        popular_drinks=popular_drinks,
    )

async def get_expiring_stocks() -> list[Stock]:
    """This function returns a list of expiring stocks"""

    # Get the list of stock without any filtering
    data = await get_inventory_stock("http://localhost:8002", 1, "EMPLOYEE")
    #get filtered result
    expiring_stocks = _filter_expiring_stocks(data, 7)

    return expiring_stocks

# Helper method to filter
def _filter_expiring_stocks(
    stocks: list[Stock],
    cutoff: int,
) -> list[Stock]:
    """
    Helper function to filter expiring stocks by the cutoff days
    (If the cutoff is 7 for example, it would return all expiring stocks that is expiring in 7 days and under)
    """

    today = date.today()
    cutoff_date = today + timedelta(days=cutoff)
    expiring_stocks: list[Stock] = []

    for stock in stocks:
        # The schema already converted these fields into Python types.
        if stock.next_expiry is None or stock.usable_quantity <= 0:
            continue

        if today <= stock.next_expiry <= cutoff_date:
            expiring_stocks.append(stock)

    return expiring_stocks

async def get_recipes_containing(
    ingredient_ids: list[int],
) -> list[Recipe]:
    """Return recipes containing at least one requested ingredient."""

    matching_recipes: list[Recipe] = []

    for recipe_data in sample_recipes:
        # Validate the dictionary and its nested ingredients.
        recipe = Recipe.model_validate(recipe_data)

        for ingredient in recipe.ingredient_ids:
            if ingredient.ingredient_id in ingredient_ids:
                matching_recipes.append(recipe)

                # One match is enough
                break

    return matching_recipes


def _has_enough_stock(
    recipe: Recipe,
    stocks: list[Stock],
) -> bool:
    """Check whether usable stock can make one serving of a recipe."""

    if not recipe.ingredient_ids:
        return False

    for ingredient in recipe.ingredient_ids:
        found = False

        for stock in stocks:
            if stock.ingredient_id == ingredient.ingredient_id:
                found = True

                # Quantities must use the same unit before comparison.
                if stock.mesure_unit != ingredient.unit:
                    return False

                if stock.usable_quantity < ingredient.quantity:
                    return False

                # This ingredient has enough stock.
                # Stop searching inventory and check the next ingredient.
                break

        # No inventory entry matched this ingredient.
        if not found:
            return False

    return True

def get_available_expiring_recipes(
    expiring_recipes: list[Recipe],
    stocks: list[Stock],
) -> list[Recipe]:
    """Keep only recipes with enough stock for one serving or more."""

    available_recipes: list[Recipe] = []

    for recipe in expiring_recipes:
        # Check every ingredient required by this recipe.
        if _has_enough_stock(recipe, stocks):
            available_recipes.append(recipe)

    return available_recipes

async def get_expiring_recipe_recommendations(
    stocks: list[Stock] | None = None,
) -> list[ExpiringDrink]:
    """Find available recipes using ingredients approaching expiry."""

    # Fetch inventory only when the caller hasn't provided it.
    if stocks is None:
        stocks = await get_inventory_stock(
            "http://localhost:8002", 1, "EMPLOYEE"
        )

    # Identify ingredients approaching expiry.
    expiring_stocks = _filter_expiring_stocks(stocks, 7)

    ingredient_ids = [
        stock.ingredient_id
        for stock in expiring_stocks
    ]

    # Find  recipes containing those ingredients.
    matching_recipes = await get_recipes_containing(ingredient_ids)

    # Keep recipes that have enough ingredients.
    available_recipes = get_available_expiring_recipes(
        matching_recipes, stocks
    )

    # Determine the date used to order each recipe.
    def expiry_sort_key(recipe: Recipe) -> date:
        expiry = _get_recipe_expiry(recipe, stocks)

        # Recipes without an expiry date would go last.
        return expiry if expiry is not None else date.max

    # Order the available recipes by their earliest ingredient expiry.
    sorted_recipes = sorted(available_recipes, key=expiry_sort_key)

    # Convert each recipe into a recommendation with an explanation.
    recommendations: list[ExpiringDrink] = []

    for recipe in sorted_recipes:
        recommendation = _build_expiring_drink(recipe, stocks)
        recommendations.append(recommendation)

    return recommendations

def _get_recipe_expiry(
    recipe: Recipe,
    stocks: list[Stock],
) -> date | None:
    """Find the earliest ingredient expiry for a recipe."""

    earliest_expiry: date | None = None

    for ingredient in recipe.ingredient_ids:
        for stock in stocks:
            if stock.ingredient_id == ingredient.ingredient_id:
                # Ignore ingredients without a dated expiry.
                if stock.next_expiry is not None:
                    if earliest_expiry is None or stock.next_expiry < earliest_expiry:
                        earliest_expiry = stock.next_expiry

                    break

    return earliest_expiry

def _build_expiring_drink(
    recipe: Recipe,
    stocks: list[Stock],
) -> ExpiringDrink:
    """Turn an expiring recipe into a recommendation with an explanation."""

    expiry = _get_recipe_expiry(recipe, stocks)

    # This helper should only receive recipes with a known expiry.
    if expiry is None:
        raise ValueError(f"Recipe {recipe.recipe_id} has no ingredient expiry date.")

    days_remaining = (expiry - date.today()).days

    if days_remaining == 0:
        reason = "One of the ingredients is expiring today."
    elif days_remaining == 1:
        reason = "One of the ingredients is expiring tomorrow."
    else:
        reason = f"One of the ingredients is expiring in {days_remaining} days."

    return ExpiringDrink(
        recipe_id=recipe.recipe_id,
        name=recipe.name,
        reason=reason,
    )

async def get_recipes_by_ids(
    recipe_ids: list[int],
) -> list[Recipe]:
    """Simulate retrieving recipes by their IDs from the recipe service."""

    matching_recipes: list[Recipe] = []

    for recipe_data in sample_recipes:
        recipe = Recipe.model_validate(recipe_data)

        # Compare the recipe's ID with the requested recipe IDs.
        if recipe.recipe_id in recipe_ids:
            matching_recipes.append(recipe)

    return matching_recipes

async def get_popular_drink_recommendations(
    stocks: list[Stock] | None = None,
) -> list[PopularDrink]:
    """Rank available drinks by servings sold, highest first."""

    sales_counts = await get_recipe_sales_counts()

    recipe_ids = [
        sales.recipe_id
        for sales in sales_counts
    ]
    recipes = await get_recipes_by_ids(recipe_ids)

    # Use all usable inventory to check recipe availability.
    if stocks is None:
        stocks = await get_inventory_stock(
            "http://localhost:8002", 1, "EMPLOYEE"
        )

    recommendations: list[PopularDrink] = []

    for recipe in recipes:
        # Skip recipes that cannot currently be prepared.
        if not _has_enough_stock(recipe, stocks):
            continue

        for sales in sales_counts:
            if sales.recipe_id == recipe.recipe_id:
                # A recipe with no sales isn't a popular recommendation.
                if sales.quantity_ordered > 0:
                    recommendations.append(
                        PopularDrink(
                            recipe_id=recipe.recipe_id,
                            name=recipe.name,
                            quantity_ordered=sales.quantity_ordered,
                        )
                    )

                break

    # Give sorted() the sales quantity to compare for each drink.
    def sales_sort_key(drink: PopularDrink) -> int:
        return drink.quantity_ordered or 0

    ranked_drinks = sorted(
        recommendations,
        key=sales_sort_key,
        reverse=True,
    )

    return ranked_drinks[:10]