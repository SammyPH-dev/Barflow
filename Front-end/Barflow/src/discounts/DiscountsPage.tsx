import Sidebar from "../navigation/Sidebar";
import type { SidebarProps } from "../navigation/Sidebar";
import "./DiscountsPage.css";

export default function DiscountsPage({ activePage, onNavigate }: SidebarProps) {
    return (
        <div className="discounts-layout">
            <Sidebar activePage={activePage} onNavigate={onNavigate} />
            <main className="discounts-page">
                <h2>Discounts</h2>
                <p>ToDo</p>
            </main>
        </div>
    );
}
