import "./TabSelection.css"

export type Tab = "supplier-orders" | "inventory"

type TabSelectionProps = {
    activeTab: Tab
    onChange: (tab: Tab) => void
}

export default function TabSelection({ activeTab, onChange }: TabSelectionProps) {
    return (
        <div className="tab-selection">
            <button type="button" aria-pressed={activeTab === "supplier-orders"} onClick={() => onChange("supplier-orders")}>
                Reorder stock
            </button>
            <button type="button" aria-pressed={activeTab === "inventory"} onClick={() => onChange("inventory")}>
                Inventory
            </button>
        </div>
    )
}
