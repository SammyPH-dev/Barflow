export type MesureUnit = "ml" | "g" | "unit"

// A recipe card. There is no recipe endpoint in the inventory service, so recipes stay mock data.
export type Recipe = {
    id: number
    name: string
    description: string
    imageUrl: string
}

// What GET /ingredients returns for one ingredient.
export type Ingredient = {
    id: number
    name: string
    mesure_unit: MesureUnit
    reorder_threshold: number
    shelf_life_days: number | null // null = never expires
}

// What GET /stock returns for one ingredient (used when the real data is connected).
// Quantities are strings like "750.000", not numbers.
export type StockLevel = {
    ingredient_id: number
    name: string
    mesure_unit: MesureUnit
    usable_quantity: string
    reorder_threshold: number
    below_threshold: boolean
    next_expiry: string | null // YYYY-MM-DD
}

// An ingredient joined with its stock: what the cards display.
export type InventoryItem = Ingredient & {
    usable_quantity: string
    below_threshold: boolean
    next_expiry: string | null
}
