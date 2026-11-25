//author: Jason Bussiere
//date:2026-11-20

export interface CartItem {
    id: string;
    name: string;
    description: string;
    modifiers?: string;
    quantity?:number;
    unitPrice: number;
}

export interface ActiveTableOrder {
    orderNumber: string;
    openedAt: string;
    tableName: string;
    serverName: string;
    guestCount: number;
    taxRate: number;
    items: CartItem[];
}

export interface OrderCartProps {
    orderNumber: string;
    openedAt: string;
    tableName: string;
    serverName: string;
    guestCount: number;
    taxRate: number;
    items: CartItem[];
    activeOrders: ActiveTableOrder[];

    //callbacks to connect with  main menu page
    onSelectedTable?: (order: ActiveTableOrder) => void;
    onUpdateQuantity: (itemId: string, newQuantity: number) => void;
    onEditItem?: (item: CartItem) => void;
    onAddNote?: () => void;
    onCheckout?: (total: number) => void;
    onSplitBill?: () => void;
}