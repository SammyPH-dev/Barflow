import DetailsPopup from "./DetailsPopup"
import { formatMoney } from "../utils/format"
import type { Recipe } from "../types"
import discountIcon from "../../assets/rabais.svg"
import editIcon from "../../assets/edit.svg"

type RecipeDetailsProps = {
    recipe: Recipe
    onClose: () => void
}


// Details of a recipe shown in a popup
export default function RecipeDetails({ recipe, onClose }: RecipeDetailsProps) {
    const isDiscounted = recipe.discountCents > 0
    const currentPrice = recipe.priceCents - recipe.discountCents

    return (
        <DetailsPopup label={`Details of ${recipe.name}`} onClose={onClose}>
            <header className="details__header">
                <h3>Details</h3>
                {isDiscounted && <span className="details__badge">On sale</span>}
            </header>

            <img className="details__image" src={recipe.imageUrl} alt={recipe.name} />

            <div className="details__body">
                <h4 className="details__name">{recipe.name}</h4>
                <p className="details__description">{recipe.description}</p>

                <dl className="details__rows">
                    <div>
                        <dt>Regular price</dt>
                        <dd>{formatMoney(recipe.priceCents)}</dd>
                    </div>
                    {isDiscounted && (
                        <div className="details__row--discount">
                            <dt>Discount</dt>
                            <dd>− {formatMoney(recipe.discountCents)}</dd>
                        </div>
                    )}
                    <div className="details__row--total">
                        <dt>Current price</dt>
                        <dd>{formatMoney(currentPrice)}</dd>
                    </div>
                </dl>
                <p className="details__note">Unit price, before taxes.</p>

                <div className="details__actions">
                    <button type="button" className="details__button" autoFocus onClick={onClose}>
                        Close
                    </button>
                    {/* TODO: enable when the discount and recipe services can be reached through the API Gateway */}
                    <button type="button" className="details__button details__button--discount" disabled title="Coming soon">
                        <img src={discountIcon} alt="" />
                        Discount
                    </button>
                    <button type="button" className="details__icon-button" disabled title="Coming soon" aria-label="Edit the recipe">
                        <img src={editIcon} alt="" />
                    </button>
                </div>
            </div>
        </DetailsPopup>
    )
}
