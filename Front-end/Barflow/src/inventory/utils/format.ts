import type { MesureUnit } from "../types"

// "10000.000" + "ml" -> "10 L", "500.000" + "g" -> "500 g"
export function formatQuantity(value: string, unit: MesureUnit): string {
    const n = Number(value)
    if (unit === "ml") return n >= 1000 ? `${n / 1000} L` : `${n} ml`
    if (unit === "g") return `${n} g`
    return `${n} ${n === 1 ? "unit" : "units"}`
}

// 1400 -> "14.00 $" built from whole numbers only to avoid float rounding errors
export function formatMoney(cents: number): string {
    const sign = cents < 0 ? "-" : ""
    const absolute = Math.abs(cents)
    const dollars = Math.floor(absolute / 100)
    const rest = String(absolute % 100).padStart(2, "0")
    return `${sign}${dollars}.${rest} $`
}

// "2026-12-30" -> "Dec 30, 2026"
export function formatDate(value: string): string {
    const [year, month, day] = value.split("-").map(Number)
    return new Date(year, month - 1, day).toLocaleDateString("en-CA", { year: "numeric", month: "short", day: "numeric" })
}
