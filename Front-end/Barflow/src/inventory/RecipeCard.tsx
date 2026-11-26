import type { Recipe } from "./types"

type RecipeCardProps = {
    recipe: Recipe
}

export default function RecipeCard({ recipe }: RecipeCardProps) {
    return (
        <article className="card">
            <img className="card__image" src={recipe.imageUrl} alt={recipe.name} />
            <h4>{recipe.name}</h4>
            <p>{recipe.description}</p>
        </article>
    )
}
