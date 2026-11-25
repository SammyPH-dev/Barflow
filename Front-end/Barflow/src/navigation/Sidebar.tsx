import { useState } from "react";
import "./Sidebar.css";
import venteIcon from "../assets/vente.svg";
import additionsIcon from "../assets/additions.svg";
import inventaireIcon from "../assets/inventaire.svg";
import activiteIcon from "../assets/activite.svg";

// Display the navigation choices for the application.
export default function Sidebar() {
    const [activePage, setActivePage] = useState("Vente");
    return (
        <nav className="sidebar" aria-label="Navigation principale">
        <button
            type="button"
            className={activePage === "Vente" ? "sidebar-active" : ""}
            onClick={() => setActivePage("Vente")}
            
        >
            <img className="sidebar-icon" src={venteIcon} alt="" />
            <span>Vente</span>
        </button>
        <button 
        type="button"
        className={activePage === "Additions" ? "sidebar-active" : ""}
        onClick={() => setActivePage("Additions")}
        >
            <img className="sidebar-icon" src={additionsIcon} alt="" />
            <span>Additions</span>
        </button>
        <button
            type="button"
            className={activePage === "Inventaire" ? "sidebar-active" : ""}
            onClick={() => setActivePage("Inventaire")}
        >
            <img className="sidebar-icon" src={inventaireIcon} alt="" />
            <span>Inventaire</span>
        </button>
        <button
            type="button"
            className={activePage === "Activité" ? "sidebar-active" : ""}
            onClick={() => setActivePage("Activité")}
        >
            <img className="sidebar-icon" src={activiteIcon} alt="" />
            <span>Activité</span>
        </button>
        </nav>
    );
}