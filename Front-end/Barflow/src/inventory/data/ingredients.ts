import rum from "../../assets/rhum.png"
import cherrySyrup from "../../assets/cherry_sirup.png"
import lime from "../../assets/lime.png"
import olives from "../../assets/olives.png"
import grapefruit from "../../assets/grapefruit.png"
import coconutMilk from "../../assets/coconut_milk.png"
import type { InventoryItem, SupplierProduct } from "../types"

// MockDB equivalent, used by both tabs.
// TODO: replace with GET /api/v1/inventory/ingredients and /stock, through the API Gateway.
export const ingredients: InventoryItem[] = [
    { id: 1, name: "Rum", mesure_unit: "ml", reorder_threshold: 750, shelf_life_days: null, usable_quantity: "10000.000", below_threshold: false, next_expiry: null, imageUrl: rum },
    { id: 2, name: "Cherry syrup", mesure_unit: "ml", reorder_threshold: 6000, shelf_life_days: 180, usable_quantity: "5000.000", below_threshold: true, next_expiry: "2027-05-20", imageUrl: cherrySyrup },
    { id: 3, name: "Lime", mesure_unit: "g", reorder_threshold: 250, shelf_life_days: 14, usable_quantity: "500.000", below_threshold: false, next_expiry: "2026-12-05", imageUrl: lime },
    { id: 4, name: "Olives", mesure_unit: "g", reorder_threshold: 300, shelf_life_days: 60, usable_quantity: "1000.000", below_threshold: false, next_expiry: "2027-01-15", imageUrl: olives },
    { id: 5, name: "Grapefruit", mesure_unit: "g", reorder_threshold: 1000, shelf_life_days: 10, usable_quantity: "2000.000", below_threshold: false, next_expiry: "2026-12-03", imageUrl: grapefruit },
    { id: 6, name: "Coconut milk", mesure_unit: "ml", reorder_threshold: 1000, shelf_life_days: 365, usable_quantity: "3000.000", below_threshold: false, next_expiry: "2027-09-10", imageUrl: coconutMilk },
]

// What the supplier sells for each ingredient, by ingredient id (mock data).
// TODO: the inventory service has no supplier catalogue: decide where the prices come from.
const supplierProducts: Record<number, SupplierProduct> = {
    1: { packageSize: 750, priceCents: 1400 }, // 750 ml bottle
    2: { packageSize: 1000, priceCents: 1400 }, // 1 L bottle
    3: { packageSize: 1000, priceCents: 800 }, // 1 kg bag
    4: { packageSize: 1000, priceCents: 1200 }, // 1 kg jar
    5: { packageSize: 2000, priceCents: 900 }, // 2 kg box
    6: { packageSize: 1000, priceCents: 600 }, // 1 L carton
}

// The package of an ingredient. An ingredient missing from the list is sold by 1 (ml, g or unit), at 0 $.
export function getSupplierProduct(ingredientId: number): SupplierProduct {
    return supplierProducts[ingredientId] ?? { packageSize: 1, priceCents: 0 }
}
