import "./Sidebar.css";
import venteIcon from "../assets/vente.svg";
import additionsIcon from "../assets/additions.svg";
import inventaireIcon from "../assets/inventaire.svg";
import rabaisIcon from "../assets/rabais.svg";
import activiteIcon from "../assets/activite.svg";

export type SidebarPage = "Sales" | "Bills" | "Inventory" | "Discounts" | "Activity";

// Props every page passes down to the sidebar.
export type SidebarProps = {
    activePage: SidebarPage;
    onNavigate: (page: SidebarPage) => void;
};

const entries: { page: SidebarPage; icon: string }[] = [
    { page: "Sales", icon: venteIcon },
    { page: "Bills", icon: additionsIcon },
    { page: "Inventory", icon: inventaireIcon },
    { page: "Discounts", icon: rabaisIcon },
    { page: "Activity", icon: activiteIcon },
];

// Display the navigation choices for the application.
export default function Sidebar({ activePage, onNavigate }: SidebarProps) {
    return (
        <nav className="sidebar" aria-label="Main navigation">
            {entries.map(({ page, icon }) => (
                <button
                    key={page}
                    type="button"
                    className={activePage === page ? "sidebar-active" : ""}
                    onClick={() => onNavigate(page)}
                >
                    <img className="sidebar-icon" src={icon} alt="" />
                    <span>{page}</span>
                </button>
            ))}
        </nav>
    );
}
