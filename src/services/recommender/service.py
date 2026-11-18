from .schemas import (Recommendations, ExpiringDrink, PopularDrink)



#A des fins de test seulement. Je n'ai pas encore fait une formule de recommendation avec des poids
def get_recommendations() -> Recommendations:
    return Recommendations(
        expiring_drinks = [ExpiringDrink(
            recipe_id = 1,
            name = "Mojito",
            reason = "Mint will expire in 5 days"
        )],
        popular_drinks = [PopularDrink(
            recipe_id = 1,
            name = "Mojito",
            quantity_ordered = 28,
        )]
    )