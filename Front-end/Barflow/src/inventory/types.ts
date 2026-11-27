export type MesureUnit = "ml" | "g" | "unit"

// A recipe card. There is no recipe endpoint yet, so recipes stay mock data.
// Money is in cents (whole numbers), never in floats: 1400 = 14.00 $.
export type Recipe = {
    id: number
    name: string
    description: string
    imageUrl: string
    priceCents: number // regular price
    discountCents: number // 0 = no discount
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
    imageUrl?: string // front end only: the inventory service has no images
}

// What the supplier sells for one ingredient: a package (ex: a 750 ml bottle) and its price.
export type SupplierProduct = {
    packageSize: number // in the unit of the ingredient (ml, g or unit)
    priceCents: number // price of one package, in cents
}

// One ingredient added to the supplier order being prepared (Reorder stock tab).
// quantity = number of packages (ex: 2 bottles of 750 ml).
export type OrderLine = {
    item: InventoryItem
    product: SupplierProduct
    quantity: number
}
