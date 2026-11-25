import { useState } from "react";
import DrinkDetails from "./DrinkDetails";
import type { DrinkCardProps } from "./types";
import "./DrinkCard.css";

/**
 * Displays a card describing one drink.
 */
export default function DrinkCard({ name, description, imageUrl, price }: DrinkCardProps) {
  const [isSelected, setIsSelected] = useState(false);

  function openDetails() {
    setIsSelected(true);
  }

  function closeDetails() {
    setIsSelected(false);
  }

  return (
    <article className="drink-card">
      <img src={imageUrl} alt={name} className="drink-card-image" />
      <h2>{name}</h2>
      <p>{description}</p>
      <p>{price} $</p>
      <button onClick={openDetails}>Voir les détails</button>

      {isSelected && (
        <DrinkDetails
          name={name}
          description={description}
          onClose={closeDetails}
          imageUrl={imageUrl}
        />
      )}
    </article>
  );
}

