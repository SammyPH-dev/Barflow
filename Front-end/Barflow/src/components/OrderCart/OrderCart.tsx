//author: Jason Bussiere
//date:2026-11-20
import type { OrderCartProps } from './types'
import './OrderCart.css'
import { useState, useEffect, useId, useRef } from 'react';

import {
    MoreHorizontal,
    Armchair,
    ChevronDown,
    Minus,
    Plus,
    Pencil,
    MessageSquarePlus,
    GitFork,
    ArrowRight,
    CreditCard,
} from 'lucide-react';




export function OrderCart({
    orderNumber,
    openedAt,
    taxRate,
    items,
    activeOrders,
    onSelectedTable,
    onUpdateQuantity,
    onEditItem,
    onAddNote,
    onCheckout,
    onSplitBill,
}: OrderCartProps) {
    
    const totalDrinks = items.reduce((sum, item) => sum + (item.quantity ?? 0), 0);
    const subtotal = items.reduce((sum, item) => sum + item.unitPrice * (item.quantity ?? 0), 0);
    const taxAmount = subtotal * taxRate;
    const totalToPay = subtotal + taxAmount;
    const [isTableMenuOpen, setIsTableMenuOpen] = useState(false);
    const menuId = useId();
    const menuWrapperRef = useRef<HTMLDivElement>(null);
    const selectorButtonRef = useRef<HTMLButtonElement>(null);

    useEffect(() => {
    if (!isTableMenuOpen) return;

    const handlePointerDown = (event: PointerEvent) => {
    if (
        event.target instanceof Node &&
        !menuWrapperRef.current?.contains(event.target)
    ) {
        setIsTableMenuOpen(false);
    }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
        if (event.key === "Escape") {
            setIsTableMenuOpen(false);
            selectorButtonRef.current?.focus();
        }
    };

    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
        document.removeEventListener("pointerdown", handlePointerDown);
        document.removeEventListener("keydown", handleKeyDown);
    };
}, [isTableMenuOpen]);


    const activeOrder = activeOrders.find(
        (order) => order.orderNumber === orderNumber,
    );

    return (
        <aside className="order-cart">
            {/* HEADER & TABLE CONTEXT */}
            <header className="cart-header">
                <div className="cart-title-row">
                    <h2>Current Order</h2>
                    <button type="button" className="icon-btn" aria-label="Options">
                        <MoreHorizontal size={20}/>
                    </button>
                </div>
                    <div className="table-selector-wrapper" ref={menuWrapperRef}>
                        <button
                            ref={selectorButtonRef}
                            type="button"
                            className="table-selector"
                            aria-expanded={isTableMenuOpen}
                            aria-controls={menuId}
                            onClick={() => setIsTableMenuOpen((open) => !open)}
                        >
                            <div className="table-selector-left">
                            <Armchair size={20} aria-hidden="true" />
                            </div>

                            <div className="table-inform">
                            <strong>{activeOrder?.tableName ?? "Select a table"}</strong>
                            {activeOrder && (
                                <span className="table-servername-guestcount">
                                {activeOrder.serverName} · {activeOrder.guestCount} guests
                                </span>
                            )}
                            </div>
                            

                            <ChevronDown size={16} className="chevron-icon" aria-hidden="true" />
                        </button>
                        <div
                            id={menuId}
                            className="table-order-menu"
                            role="group"
                            aria-label="Active table orders"
                            hidden={!isTableMenuOpen}
                        >
                            {activeOrders.length === 0 ? (
                            <p className="table-order-empty">No active table orders</p>
                            ) : (
                            activeOrders.map((order) => (
                                <button
                                key={order.orderNumber}
                                type="button"
                                className="table-order-option"
                                aria-pressed={order.orderNumber === orderNumber}
                                onClick={() => {
                                    onSelectedTable?.(order);
                                    setIsTableMenuOpen(false);
                                    selectorButtonRef.current?.focus();
                                }}
                                >
                                <Armchair size={18} aria-hidden="true" />
                                <span>
                                    <strong>{order.tableName}</strong>
                                    <small>
                                    {order.orderNumber} · {order.serverName}
                                    </small>
                                </span>
                                </button>
                            ))
                            )}
                        </div>
                        </div>

                <div className="table-order-number">
                    <span >
                        {orderNumber} - Opened at: {openedAt}
                    </span>
                </div>
            </header>

            {/* ITEMS LIST */}
            <section className="cart-items">
                <div className="round-header">
                    <span className="round-title">NEW ORDER</span>
                    <span>
                        {totalDrinks} {totalDrinks > 1 ? 'drinks' : 'drink'}
                    </span>
                </div>

                {items.length === 0 ? (
                    <p className="item-modifiers">No items on the order</p>
                ) : (
                    <ul className="cart-items-list">
                        {items.map((item) => (
                            <li key={item.id} className="cart-item">
                            <div className="item-top-row">
                                <strong>{item.name}</strong>
                                <span>{(item.unitPrice * (item.quantity ?? 0)).toFixed(2)} $</span>
                            </div>
                            <span className="item-desc-label">{item.description}</span>

                            {item.modifiers && <p className="item-modifiers">{item.modifiers}</p>}

                            <div className="item-control-rows">
                                <div className="quantity-stepper">
                                    <button type="button" onClick={() =>
                                        onUpdateQuantity(item.id, (item.quantity ?? 0) - 1)
                                    } aria-label="remove"> <Minus size={14} />
                                    </button>
                                    <span>{item.quantity ?? 0}</span>
                                    <button type="button" onClick={() =>
                                        onUpdateQuantity(item.id, (item.quantity ?? 0) + 1)
                                    } aria-label="add"> <Plus size={14} />
                                    </button>
                                </div>

                                <span className="unit-price">{item.unitPrice.toFixed(2)} $ each</span>

                                <button type="button" className="icon-btn" onClick={() => onEditItem?.(item)}
                                aria-label={`Modifer ${item.name}`}> <Pencil size={14} />
                                </button>
                            </div>
                        </li>
                        ))}
                    </ul>
                )}

                <button type="button" className="add-note-btn" onClick={onAddNote}>
                    <MessageSquarePlus size={16} /><span className="add-note-label">Add note</span>
                </button>
            </section>

            {/* TOTALS */}
            <section className="cart-totals">
                <div className="total-row">
                    <span>Subtotal</span>
                    <span>{subtotal.toFixed(2)} $</span>
                </div>
                <div className="total-row">
                    <span>Sales tax ({Math.round(taxRate * 100)} %)</span>
                    <span>{taxAmount.toFixed(2)} $</span>
                </div>
                
                <div className="grand-total-row">
                    <strong>Total</strong>
                    <strong>{totalToPay.toFixed(2)} $</strong>
                </div>
            </section>
            
            <div className="primary-checkout">
                <button type="button" className="primary-checkout-btn" onClick={() => onCheckout?.(totalToPay)}>
                        <span className="checkout-label"><CreditCard size={14} />  Pay {totalToPay.toFixed(2)}</span>
                        <span><ArrowRight size={14} /></span>
                </button>
            </div>
            
            {/* FOOTER ACTIONS */}
            <footer className="cart-actions">
                <div className="secondary-action">
                    <button type="button" className="utility-btn" onClick={onSplitBill}>
                        <GitFork size={14} style={{transform: 'rotate(90deg)'}}/>
                        <span>Split the bill</span>
                    </button>
                </div>
            </footer>
        </aside>
    );
}