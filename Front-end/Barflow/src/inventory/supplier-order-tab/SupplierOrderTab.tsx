import { useState } from "react"
import { ArrowRight, ChevronDown, CreditCard, Minus, MoreHorizontal, Package, Plus } from "lucide-react"
import { formatMoney, formatQuantity } from "../utils/format"
import type { InventoryItem, OrderLine } from "../types"
import "./SupplierOrderTab.css"

const SALES_TAX_PERCENT = 14.975

type SupplierOrderTabProps = {
    ingredients: InventoryItem[]
    lines: OrderLine[] // ingredients added with "+" (here or in the Inventory tab)
    orderNumber: number
    confirmation: string | null // message shown after an order is placed
    onAdd: (item: InventoryItem) => void
    onChangeQuantity: (ingredientId: number, change: number) => void
    onOrder: (ingredientIds: number[]) => void
}

// Today's date as YYYY-MM-DD, in local time
function today(): string {
    const now = new Date()
    const month = String(now.getMonth() + 1).padStart(2, "0")
    const day = String(now.getDate()).padStart(2, "0")
    return `${now.getFullYear()}-${month}-${day}`
}


// Reorder stock tab: the supplier order being prepared
export default function SupplierOrderTab({ ingredients, lines, orderNumber, confirmation, onAdd, onChangeQuantity, onOrder }: SupplierOrderTabProps) {
    const [isExpanded, setIsExpanded] = useState(true) // the order details are shown
    const [isPicking, setIsPicking] = useState(false) // the list to add an ingredient is shown

    // Money is in cents (whole numbers) to avoid float rounding errors
    const subtotalCents = lines.reduce((sum, line) => sum + line.product.priceCents * line.quantity, 0)
    const taxCents = Math.round((subtotalCents * SALES_TAX_PERCENT) / 100)
    const totalCents = subtotalCents + taxCents

    const addedIds = lines.map((line) => line.item.id)
    const notAdded = ingredients.filter((item) => !addedIds.includes(item.id))
    const lowStock = notAdded.filter((item) => item.below_threshold) // suggested: under their reorder threshold

    function addFromList(ingredientId: string) {
        const item = ingredients.find((ingredient) => ingredient.id === Number(ingredientId))
        if (item) {
            onAdd(item)
        }
        setIsPicking(false)
    }

    return (
        <div className="inventory_main supplier-order">
            <div className="supplier-order__title">
                <h2>Orders</h2>
                {/* TODO: options (if we have time. Otherwise needs to be removed) */}
                <button type="button" className="supplier-order__icon-btn" aria-label="Options" disabled title="Coming soon">
                    <MoreHorizontal size={20} />
                </button>
            </div>

            <h3 className="supplier-order__subtitle">Smart recommendations</h3>
            {lowStock.length > 0 && (
                <ul className="supplier-order__suggestions">
                    {lowStock.map((item) => (
                        <li key={item.id}>
                            <span>
                                {item.name} <span className="supplier-order__low">· low stock</span>
                            </span>
                            <button type="button" className="supplier-order__small-btn" onClick={() => onAdd(item)} aria-label={`Add ${item.name} to the order`}>
                                <Plus size={14} />
                            </button>
                        </li>
                    ))}
                </ul>
            )}

            <div className="supplier-order__selector-wrapper">
                <button
                    type="button"
                    className="supplier-order__selector"
                    aria-expanded={isExpanded}
                    aria-controls="supplier-order-lines"
                    onClick={() => setIsExpanded(!isExpanded)}
                >
                    <div className="supplier-order__selector-icon">
                        <Package size={20} aria-hidden="true" />
                    </div>
                    <div className="supplier-order__selector-info">
                        <strong>Order #{String(orderNumber).padStart(5, "0")}</strong>
                        <span>Date: {today()}</span>
                    </div>
                    <ChevronDown size={16} className={isExpanded ? "supplier-order__chevron" : "supplier-order__chevron supplier-order__chevron--closed"} aria-hidden="true" />
                </button>
            </div>

            {confirmation && <p className="supplier-order__confirmation" role="status">{confirmation}</p>}

            <div id="supplier-order-lines" hidden={!isExpanded}>
                {lines.length === 0 ? (
                    <p className="supplier-order__empty">
                        No ingredient in the order. Use "+" on an ingredient in the Inventory tab, or below.
                    </p>
                ) : (
                    <ul className="supplier-order__lines">
                        {lines.map((line) => (
                            <li key={line.item.id} className="supplier-order__line">
                                <div className="supplier-order__line-top">
                                    <strong>{line.item.name}</strong>
                                    <span>{formatMoney(line.product.priceCents * line.quantity)}</span>
                                </div>

                                <div className="supplier-order__line-controls">
                                    <div className="supplier-order__stepper">
                                        <button type="button" aria-label={`Remove 1 ${line.item.name}`} onClick={() => onChangeQuantity(line.item.id, -1)}>
                                            <Minus size={14} />
                                        </button>
                                        <span>{line.quantity}</span>
                                        <button type="button" aria-label={`Add 1 ${line.item.name}`} onClick={() => onChangeQuantity(line.item.id, 1)}>
                                            <Plus size={14} />
                                        </button>
                                    </div>

                                    <span className="supplier-order__unit-price">
                                        {formatMoney(line.product.priceCents)} each ({formatQuantity(String(line.product.packageSize), line.item.mesure_unit)})
                                    </span>

                                    <button type="button" className="supplier-order__order-btn supplier-order__order-btn--line" onClick={() => onOrder([line.item.id])}>
                                        <span className="supplier-order__order-label">
                                            <CreditCard size={14} /> Order
                                        </span>
                                        <ArrowRight size={14} />
                                    </button>
                                </div>
                            </li>
                        ))}
                    </ul>
                )}

                {/* "+" under the lines: add another ingredient to the order */}
                {notAdded.length > 0 && (
                    <div className="supplier-order__add">
                        <button
                            type="button"
                            className="supplier-order__small-btn"
                            aria-label="Add an ingredient to the order"
                            aria-expanded={isPicking}
                            onClick={() => setIsPicking(!isPicking)}
                        >
                            <Plus size={14} />
                        </button>
                        {isPicking && (
                            <select
                                className="supplier-order__select"
                                aria-label="Ingredient to add"
                                value=""
                                onChange={(event) => addFromList(event.target.value)}
                            >
                                <option value="" disabled>
                                    Choose an ingredient…
                                </option>
                                {notAdded.map((item) => (
                                    <option key={item.id} value={item.id}>
                                        {item.name}
                                    </option>
                                ))}
                            </select>
                        )}
                    </div>
                )}
            </div>

            <section className="supplier-order__totals">
                <div className="supplier-order__total-row">
                    <span>Subtotal</span>
                    <span>{formatMoney(subtotalCents)}</span>
                </div>
                <div className="supplier-order__total-row">
                    <span>Sales tax ({SALES_TAX_PERCENT} %)</span>
                    <span>{formatMoney(taxCents)}</span>
                </div>
                <div className="supplier-order__grand-total">
                    <strong>Total to pay</strong>
                    <strong>{formatMoney(totalCents)}</strong>
                </div>
            </section>

            <button
                type="button"
                className="supplier-order__order-btn supplier-order__order-btn--all"
                disabled={lines.length === 0}
                onClick={() => onOrder(addedIds)}
            >
                <span className="supplier-order__order-label">
                    <CreditCard size={14} /> Order all the ingredients
                </span>
                <ArrowRight size={14} />
            </button>
        </div>
    )
}
