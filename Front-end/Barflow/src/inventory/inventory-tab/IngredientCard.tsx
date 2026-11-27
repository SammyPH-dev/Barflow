import { useState } from "react"
import IngredientDetails from "../card-details/IngredientDetails"
import { formatQuantity } from "../utils/format"
import type { InventoryItem } from "../types"

type IngredientCardProps = {
    item: InventoryItem
    onAdd: () => void // "+": adds 1 of this ingredient to the supplier order
}

/**
 * An ingredient card. Clicking it opens the details in a popup
 * The "+" button adds the ingredient to the supplier order (Reorder stock tab)
 */
export default function IngredientCard({ item, onAdd }: IngredientCardProps) {
    const [isSelected, setIsSelected] = useState(false)

    function openDetails() {
        setIsSelected(true)
    }

    function closeDetails() {
        setIsSelected(false)
    }

    // The "+" button is placed over the card with CSS, but it is not inside the card's button
    return (
        <article className="ingredient-card">
            <button type="button" className="card card--clickable" aria-haspopup="dialog" onClick={openDetails}>
                {item.imageUrl && <img className="card__image" src={item.imageUrl} alt="" />}
                <span className="card__title">{item.name}</span>
                <span className={item.below_threshold ? "card__text card__quantity--low" : "card__text"}>
                    {formatQuantity(item.usable_quantity, item.mesure_unit)}
                    {item.below_threshold && " · low stock"}
                </span>
            </button>

            <button
                type="button"
                className="ingredient-card__add"
                aria-label={`Add 1 ${item.name} to the supplier order`}
                title="Add to the supplier order"
                onClick={onAdd}
            >
                +
            </button>

            {isSelected && <IngredientDetails item={item} onClose={closeDetails} />}
        </article>
    )
}
