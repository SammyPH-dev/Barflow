import { useState } from "react"
import RecipeDetails from "../card-details/RecipeDetails"
import type { Recipe } from "../types"

type RecipeCardProps = {
    recipe: Recipe
}

// A recipe card. Clicking it opens the details in a popup
export default function RecipeCard({ recipe }: RecipeCardProps) {
    const [isSelected, setIsSelected] = useState(false)

    function openDetails() {
        setIsSelected(true)
    }

    function closeDetails() {
        setIsSelected(false)
    }

    return (
        <article>
            <button type="button" className="card card--clickable" aria-haspopup="dialog" onClick={openDetails}>
                <img className="card__image" src={recipe.imageUrl} alt="" />
                <span className="card__title">{recipe.name}</span>
                <span className="card__text">{recipe.description}</span>
            </button>

            {isSelected && <RecipeDetails recipe={recipe} onClose={closeDetails} />}
        </article>
    )
}
