import IngredientCard from "./IngredientCard"
import RecipeCard from "./RecipeCard"
import type { InventoryItem, Recipe } from "../types"
import "./InventoryTab.css"

type InventoryTabProps = {
    recipes: Recipe[]
    ingredients: InventoryItem[]
    onAddToOrder: (item: InventoryItem) => void // "+" on an ingredient card
}

export default function InventoryTab({ recipes, ingredients, onAddToOrder }: InventoryTabProps) {
    return (
        <div className="inventory_main">

            <h2>Inventory</h2>
            
            <section>
                <h3>Recipes</h3>
                <div className="card-grid">
                    {recipes.map((recipe) => (
                        <RecipeCard key={recipe.id} recipe={recipe} />
                    ))}
                </div>
            </section>

            <section>
                <h3>Ingredients</h3>
                <div className="card-grid">
                    {ingredients.map((item) => (
                        <IngredientCard key={item.id} item={item} onAdd={() => onAddToOrder(item)} />
                    ))}
                </div>
            </section>
        </div>
    )
}
