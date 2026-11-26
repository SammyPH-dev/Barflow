import type { MesureUnit } from "./types"

// "10000.000" + "ml" -> "10 L", "500.000" + "g" -> "500 g"
export function formatQuantity(value: string, unit: MesureUnit): string {
    const n = Number(value)
    if (unit === "ml") return n >= 1000 ? `${n / 1000} L` : `${n} ml`
    if (unit === "g") return `${n} g`
    return `${n} ${n === 1 ? "unit" : "units"}`
}
