import { useState } from "react"
import Sidebar from "../navigation/Sidebar"
import type { SidebarProps } from "../navigation/Sidebar"
import TabSelection from "./TabSelection"
import type { Tab } from "./TabSelection"
import SupplierOrderTab from "./SupplierOrderTab"
import InventoryTab from "./InventoryTab"
import "./InventoryPage.css"

export default function InventoryPage({ activePage, onNavigate }: SidebarProps) {
    const [activeTab, setActiveTab] = useState<Tab>("inventory")

    return (
        <div className="inventory-layout">
            <Sidebar activePage={activePage} onNavigate={onNavigate} />
            <main className="inventory-page">
                <TabSelection activeTab={activeTab} onChange={setActiveTab} />
                {activeTab === "supplier-orders" ? <SupplierOrderTab /> : <InventoryTab />}
            </main>
        </div>
    )
}
