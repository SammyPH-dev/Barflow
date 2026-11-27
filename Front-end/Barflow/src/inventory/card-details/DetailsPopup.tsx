import { useEffect, useRef } from "react"
import type { MouseEvent, ReactNode, SyntheticEvent } from "react"
import "./DetailsPopup.css"

type DetailsPopupProps = {
    label: string
    onClose: () => void
    children: ReactNode
}


// Popup shown on top of the page, used by the recipe and ingredient details
export default function DetailsPopup({ label, onClose, children }: DetailsPopupProps) {
    const dialogRef = useRef<HTMLDialogElement>(null)

    // Opens the popup when it appears, and closes it when it is removed
    useEffect(() => {
        const dialog = dialogRef.current
        if (dialog) {
            dialog.showModal()
        }

        return () => {
            if (dialog) {
                dialog.close()
            }
        }
    }, [])

    // Escape key: the browser would close the popup by itself without telling React,
    // and the card could not open it again. So the browser's closing is cancelled
    // and the parent closes it instead
    function handleCancel(event: SyntheticEvent<HTMLDialogElement>) {
        event.preventDefault()
        onClose()
    }

    // A click on the dark background around the popup closes it
    // The background counts as the <dialog> itself
    function handleClick(event: MouseEvent<HTMLDialogElement>) {
        if (event.target === event.currentTarget) {
            onClose()
        }
    }

    return (
        <dialog
            ref={dialogRef}
            aria-label={label}
            className="details-popup"
            onCancel={handleCancel}
            onClick={handleClick}
        >
            <div className="details-popup__content">{children}</div>
        </dialog>
    )
}
