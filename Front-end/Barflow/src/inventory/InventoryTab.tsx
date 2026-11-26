import IngredientCard from "./IngredientCard"
import RecipeCard from "./RecipeCard"
import { recipes } from "./recipes"
import type { InventoryItem } from "./types"
import "./InventoryTab.css"

// MockDB equivalent. Replaced by the real data when the inventory service is connected.
const ingredients: InventoryItem[] = [
    { id: 1, name: "Rhum", mesure_unit: "ml", reorder_threshold: 750, shelf_life_days: null, usable_quantity: "10000.000", below_threshold: false, next_expiry: null },
    { id: 2, name: "Sirop de cerise", mesure_unit: "ml", reorder_threshold: 500, shelf_life_days: 180, usable_quantity: "300.000", below_threshold: true, next_expiry: "2026-12-30" },
    { id: 3, name: "Lime", mesure_unit: "unit", reorder_threshold: 10, shelf_life_days: 14, usable_quantity: "25.000", below_threshold: false, next_expiry: "2026-12-05" },
]

export default function InventoryTab() {
    return (
        <div>
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
                        <IngredientCard key={item.id} item={item} />
                    ))}
                </div>
            </section>
        </div>
    )
}
