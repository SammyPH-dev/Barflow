import { useState } from "react"
import Sidebar from "../navigation/Sidebar"
import type { SidebarProps } from "../navigation/Sidebar"
import TabSelection from "./tabs/TabSelection"
import type { Tab } from "./tabs/TabSelection"
import SupplierOrderTab from "./supplier-order-tab/SupplierOrderTab"
import InventoryTab from "./inventory-tab/InventoryTab"
import { getSupplierProduct, ingredients } from "./data/ingredients"
import { recipes } from "./data/recipes"
import type { InventoryItem, OrderLine } from "./types"
import "./InventoryPage.css"

export default function InventoryPage({ activePage, onNavigate }: SidebarProps) {
    const [activeTab, setActiveTab] = useState<Tab>("inventory")

    // The supplier order being prepared. It is kept here, in the page, and not in a tab:
    // a tab is removed when the other one is shown, and its state would be lost
    const [orderLines, setOrderLines] = useState<OrderLine[]>([])
    const [orderNumber, setOrderNumber] = useState(1) // TODO: given by the inventory service
    const [confirmation, setConfirmation] = useState<string | null>(null)

    // "+" (on an ingredient card or in the Reorder stock tab) adds 1 package of that ingredient
    function addToOrder(item: InventoryItem) {
        setConfirmation(null)
        setOrderLines((lines) => {
            const alreadyAdded = lines.some((line) => line.item.id === item.id)
            if (alreadyAdded) {
                // if already in the order, adds 1 more
                return lines.map((line) =>
                    line.item.id === item.id ? { ...line, quantity: line.quantity + 1 } : line
                )
            }
            return [...lines, { item, product: getSupplierProduct(item.id), quantity: 1 }]
        })
    }

    // "-" / "+" of a line. A line that reaches 0 is removed from the order
    function changeQuantity(ingredientId: number, change: number) {
        setConfirmation(null)
        setOrderLines((lines) =>
            lines
                .map((line) => (line.item.id === ingredientId ? { ...line, quantity: line.quantity + change } : line))
                .filter((line) => line.quantity > 0)
        )
    }

    // "Order" on one line, or "Order all the ingredients"
    // TODO: send POST /api/v1/inventory/supplier-orders through the API Gateway (Manager only),
    // and only remove the lines once the service has accepted the order
    function placeOrder(ingredientIds: number[]) {
        const ordered = orderLines.filter((line) => ingredientIds.includes(line.item.id))
        if (ordered.length === 0) return

        const names = ordered.map((line) => line.item.name).join(", ")
        setConfirmation(`Order #${String(orderNumber).padStart(5, "0")} placed: ${names}.`)
        setOrderNumber(orderNumber + 1)
        setOrderLines(orderLines.filter((line) => !ingredientIds.includes(line.item.id)))
    }

    return (
        <div className="inventory-layout">
            <Sidebar activePage={activePage} onNavigate={onNavigate} />
            <main className="inventory-page">
                <TabSelection activeTab={activeTab} onChange={setActiveTab} orderCount={orderLines.length} />
                {activeTab === "supplier-orders" ? (
                    <SupplierOrderTab
                        ingredients={ingredients}
                        lines={orderLines}
                        orderNumber={orderNumber}
                        confirmation={confirmation}
                        onAdd={addToOrder}
                        onChangeQuantity={changeQuantity}
                        onOrder={placeOrder}
                    />
                ) : (
                    <InventoryTab recipes={recipes} ingredients={ingredients} onAddToOrder={addToOrder} />
                )}
            </main>
        </div>
    )
}
