import Sidebar from "../navigation/Sidebar";
import type { SidebarProps } from "../navigation/Sidebar";
import "./BillsPage.css";

export default function BillsPage({ activePage, onNavigate }: SidebarProps) {
    return (
        <div className="bills-layout">
            <Sidebar activePage={activePage} onNavigate={onNavigate} />
            <main className="bills-page">
                <h2>Bills</h2>
                <p>ToDo</p>
            </main>
        </div>
    );
}
