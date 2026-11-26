import { formatQuantity } from "./format"
import type { InventoryItem } from "./types"

type IngredientCardProps = {
    item: InventoryItem
}

export default function IngredientCard({ item }: IngredientCardProps) {
    return (
        <article className="card">
            <h4>{item.name}</h4>
            <p className={item.below_threshold ? "card__quantity card__quantity--low" : "card__quantity"}>
                {formatQuantity(item.usable_quantity, item.mesure_unit)}
                {item.below_threshold && " · low stock"}
            </p>
        </article>
    )
}
