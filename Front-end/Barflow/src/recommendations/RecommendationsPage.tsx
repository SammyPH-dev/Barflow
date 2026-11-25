import RecommendationSection from "./RecommendationSection";
import DrinkCard from "./DrinkCard";
import margaritaImage from "../assets/margarita.png";
import negroniImage from "../assets/negroni.png";
import Sidebar from "../navigation/Sidebar";
import "./RecommendationsPage.css";

// MockDB equivalent
const expiringDrinks = [
  {
    id: 1,
    name: "Negroni",
    description: "Gin · Campari · Vermouth rouge",
    imageUrl: negroniImage,
    price: 15,
  },
];

const popularDrinks = [
  {
    id: 1,
    name: "Margarita",
    description: "Tequila blanco · citron vert · agave",
    imageUrl: margaritaImage,
    price: 14,
  },
];

/**
 * Displays the recommendations page.
 */
export default function RecommendationsPage() {
  return (
    <div className="recommendations-layout">
      <Sidebar />
      <main className="recommendations-page">
        <RecommendationSection
          title="À privilégier"
          description="Des breuvages utilisant des ingrédients proches de leur péremption."
        >
        {expiringDrinks.map((drink) => (
          <DrinkCard
            key={drink.id}
            name={drink.name}
            description={drink.description}
            imageUrl={drink.imageUrl}
            price={drink.price}
          />
        ))}      
  </RecommendationSection>
        <RecommendationSection
          title="Populaires"
          description="Les breuvages les plus commandés."
        >
        {popularDrinks.map((drink) => (
          <DrinkCard
            key={drink.id}
            name={drink.name}
            description={drink.description}
            imageUrl={drink.imageUrl}
            price={drink.price}
          />
        ))}
        </RecommendationSection>
      </main>
    </div>
  );
}