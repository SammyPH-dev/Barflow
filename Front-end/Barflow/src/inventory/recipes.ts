import margarita from "../assets/margarita.png"
import negroni from "../assets/negroni.png"
import oldFashioned from "../assets/old_fashion.png"
import paloma from "../assets/paloma.png"
import espressoMartini from "../assets/espresso_martini.png"
import lagerMaison from "../assets/lager_maison.png"
import type { Recipe } from "./types"

// TODO: replace with a call to the recipe service, through the API Gateway, when it exists.
export const recipes: Recipe[] = [
    { id: 1, name: "Old Fashioned", description: "Bourbon · bitters · cane sugar", imageUrl: oldFashioned },
    { id: 2, name: "Margarita", description: "Blanco tequila · lime · agave", imageUrl: margarita },
    { id: 3, name: "Espresso Martini", description: "Vodka · coffee liqueur · espresso", imageUrl: espressoMartini },
    { id: 4, name: "Negroni", description: "Gin · Campari · sweet vermouth", imageUrl: negroni },
    { id: 5, name: "House lager", description: "Draft · 16 oz · 4.8% ABV", imageUrl: lagerMaison },
    { id: 6, name: "Paloma", description: "Tequila · grapefruit · soda water", imageUrl: paloma },
]
