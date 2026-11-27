import DetailsPopup from "./DetailsPopup"
import { formatDate, formatQuantity } from "../utils/format"
import type { InventoryItem } from "../types"
import editIcon from "../../assets/edit.svg"

type IngredientDetailsProps = {
    item: InventoryItem
    onClose: () => void
}


// Details of an ingredient shown in a popup
export default function IngredientDetails({ item, onClose }: IngredientDetailsProps) {
    return (
        <DetailsPopup label={`Details of ${item.name}`} onClose={onClose}>
            <header className="details__header">
                <h3>Details</h3>
                {item.below_threshold && <span className="details__badge">Low stock</span>}
            </header>

            {item.imageUrl && <img className="details__image" src={item.imageUrl} alt={item.name} />}

            <div className="details__body">
                <h4 className="details__name">{item.name}</h4>

                <dl className="details__rows">
                    <div className={item.below_threshold ? "details__row--total details__row--low" : "details__row--total"}>
                        <dt>In stock</dt>
                        <dd>{formatQuantity(item.usable_quantity, item.mesure_unit)}</dd>
                    </div>
                    <div>
                        <dt>Reorder threshold</dt>
                        <dd>{formatQuantity(String(item.reorder_threshold), item.mesure_unit)}</dd>
                    </div>
                    <div>
                        <dt>Shelf life</dt>
                        <dd>{item.shelf_life_days === null ? "Does not expire" : `${item.shelf_life_days} days`}</dd>
                    </div>
                    <div>
                        <dt>Next expiry</dt>
                        <dd>{item.next_expiry === null ? "—" : formatDate(item.next_expiry)}</dd>
                    </div>
                </dl>
                <p className="details__note">Usable stock only: expired lots are not counted.</p>

                <div className="details__actions">
                    <button type="button" className="details__button" autoFocus onClick={onClose}>
                        Close
                    </button>
                    {/* TODO: enable when the page is connected to the inventory service (PATCH /ingredients, Manager only) */}
                    <button type="button" className="details__icon-button" disabled title="Coming soon" aria-label="Edit the ingredient">
                        <img src={editIcon} alt="" />
                    </button>
                </div>
            </div>
        </DetailsPopup>
    )
}
