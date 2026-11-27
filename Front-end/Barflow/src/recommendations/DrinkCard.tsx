import { useState } from "react";
import DrinkDetails from "./DrinkDetails";
import type { DrinkCardProps } from "./types";
import "./DrinkCard.css";

/**
 * Displays a card describing one drink.
 */
export default function DrinkCard({
  name,
  description,
  imageUrl,
  price,
}: DrinkCardProps) {
  const [isSelected, setIsSelected] = useState(false);

  function openDetails() {
    setIsSelected(true);
  }

  function closeDetails() {
    setIsSelected(false);
  }

  return (
    <article className="drink-card">
      {imageUrl && (
        <img
          className="drink-card-image"
          src={imageUrl}
          alt={name}
        />
      )}

      <h2>{name}</h2>
      <p>{description}</p>

      {price !== undefined && <p>{price} $</p>}

      {imageUrl && (
        <button type="button" onClick={openDetails}>
          View details
        </button>
      )}
      {isSelected && imageUrl && (
        <DrinkDetails
          name={name}
          description={description}
          imageUrl={imageUrl}
          onClose={closeDetails}
        />
      )}
    </article>
  );
}

