import "./TabSelection.css"

export type Tab = "supplier-orders" | "inventory"

type TabSelectionProps = {
    activeTab: Tab
    onChange: (tab: Tab) => void
    orderCount: number // ingredients added to the supplier order
}

export default function TabSelection({ activeTab, onChange, orderCount }: TabSelectionProps) {
    return (
        <div className="tab-selection">
            <button type="button" aria-pressed={activeTab === "supplier-orders"} onClick={() => onChange("supplier-orders")}>
                Reorder stock
                {orderCount > 0 && <span className="tab-selection__count">{orderCount}</span>}
            </button>
            <button type="button" aria-pressed={activeTab === "inventory"} onClick={() => onChange("inventory")}>
                Inventory
            </button>
        </div>
    )
}
