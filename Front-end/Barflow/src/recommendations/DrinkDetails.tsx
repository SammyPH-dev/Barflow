import { useEffect, useRef } from "react";
import type { DrinkDetailsProps } from "./types";
import "./DrinkDetails.css";

export default function DrinkDetails({
  name,
  description,
  onClose,
  imageUrl
}: DrinkDetailsProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);

    useEffect(() => {
    const dialog = dialogRef.current;
    if (dialog) {
      dialog.showModal();
    }

    return () => {
      if (dialog) {
        dialog.close();
      }
    }

  }, []);

  return (
    <dialog 
      ref={dialogRef}
      aria-label={`Details de ${name}`}
      className="drink-modal"
      >
        <h3>Details de {name}</h3>
        <p>{description}</p>
        <img src={imageUrl} alt={`Image de ${name}`} className="drink-modal-image"/>
        <button autoFocus onClick={onClose}>Fermer</button>
    </dialog>
  );
}

