import margarita from "../../assets/margarita.png"
import negroni from "../../assets/negroni.png"
import oldFashioned from "../../assets/old_fashion.png"
import paloma from "../../assets/paloma.png"
import espressoMartini from "../../assets/espresso_martini.png"
import lagerMaison from "../../assets/lager_maison.png"
import type { Recipe } from "../types"

// TODO: replace with a call to the recipe service (prices) and the discount service, through the API Gateway, when they exist.
export const recipes: Recipe[] = [
    { id: 1, name: "Old Fashioned", description: "Bourbon · bitters · cane sugar", imageUrl: oldFashioned, priceCents: 1500, discountCents: 0 },
    { id: 2, name: "Margarita", description: "Blanco tequila · lime · agave", imageUrl: margarita, priceCents: 1400, discountCents: 400 },
    { id: 3, name: "Espresso Martini", description: "Vodka · coffee liqueur · espresso", imageUrl: espressoMartini, priceCents: 1600, discountCents: 0 },
    { id: 4, name: "Negroni", description: "Gin · Campari · sweet vermouth", imageUrl: negroni, priceCents: 1500, discountCents: 0 },
    { id: 5, name: "House lager", description: "Draft · 16 oz · 4.8% ABV", imageUrl: lagerMaison, priceCents: 800, discountCents: 0 },
    { id: 6, name: "Paloma", description: "Tequila · grapefruit · soda water", imageUrl: paloma, priceCents: 1300, discountCents: 0 },
]
