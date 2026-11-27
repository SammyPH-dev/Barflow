import Sidebar from "../navigation/Sidebar";
import type { SidebarProps } from "../navigation/Sidebar";
import "./ActivityPage.css";

export default function ActivityPage({ activePage, onNavigate }: SidebarProps) {
    return (
        <div className="activity-layout">
            <Sidebar activePage={activePage} onNavigate={onNavigate} />
            <main className="activity-page">
                <h2>Activity</h2>
                <p>ToDo</p>
            </main>
        </div>
    );
}
