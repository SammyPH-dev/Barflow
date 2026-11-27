import { useEffect, useState } from "react";
import { getRecommendations } from "./recommendationsApi";
import type { RecommendationsResponse } from "./types";
import RecommendationSection from "./RecommendationSection";
import DrinkCard from "./DrinkCard";
import { OrderCart } from "../components/OrderCart";
import type { CartItem } from "../components/OrderCart";
import Sidebar from "../navigation/Sidebar";
import type { SidebarProps } from "../navigation/Sidebar";
import "./RecommendationsPage.css";
import margaritaImage from "../assets/margarita.png";
import negroniImage from "../assets/negroni.png";

const items: CartItem[] = [
    {
      id: '1',
      name: 'Negroni',
      description: 'Gin, vermouth, Campari',
      quantity: 1,
      unitPrice: 12,
    },
  ]

/**
 * Displays the recommendations page.
 */
export default function RecommendationsPage({ activePage, onNavigate }: SidebarProps) {
    // Store the API response. null means no response has been loaded yet.
  const [recommendations, setRecommendations] = useState<RecommendationsResponse | null>(null);

  // Store a message if the request fails.
  const [recommendationsError, setRecommendationsError] = useState<string | null>(null);

  useEffect(() => {
    // Ignore results if this component is removed before the request finishes.
    let ignore = false;

    async function loadRecommendations() {
      try {
        // An empty base URL sends the request through our Vite proxy.
        const data = await getRecommendations("");

        if (!ignore) {
          setRecommendations(data);
        }
      } catch {
        if (!ignore) {
          setRecommendationsError("Unable to load recommendations.");
        }
      }
    }

    loadRecommendations();

    return () => {
      ignore = true;
    };
  }, []);
  return (
    <div className="recommendations-layout">
      <Sidebar activePage={activePage} onNavigate={onNavigate} />

      <main className="recommendations-page">

        {recommendationsError && (
          <p role="alert">{recommendationsError}</p>
        )}

        {recommendations === null && recommendationsError === null && (
          <p>Loading recommendations...</p>
        )}

        <RecommendationSection
          title="Use Soon"
          description="Drinks made with ingredients approaching their expiry date."
        >
          {recommendations?.expiring_drinks.map((drink) => (
            <DrinkCard
              key={drink.recipe_id}
              name={drink.name}
              description={drink.reason}
            />
          ))}     
        </RecommendationSection>
        <RecommendationSection
          title="Popular"
          description="The most frequently ordered drinks."
        >
          {recommendations?.popular_drinks.map((drink) => (
            <DrinkCard
              key={drink.recipe_id}
              name={drink.name}
              description={
                drink.quantity_ordered === null
                  ? "Sales quantity unavailable"
                  : `${drink.quantity_ordered} servings sold`
              }
            />
          ))}
        </RecommendationSection>
        {/* Temporary examples showing every DrinkCard prop. */}
        <RecommendationSection
          title="Card Preview"
          description="Examples with images and prices."
        >
          <DrinkCard
            name="Margarita"
            description="Blanco tequila · triple sec · lime juice"
            imageUrl={margaritaImage}
            price={14}
          />

          <DrinkCard
            name="Negroni"
            description="Gin · Campari · red vermouth"
            imageUrl={negroniImage}
            price={15}
          />
        </RecommendationSection>
      </main>
      <OrderCart 
          orderNumber="ORD-001"
          openedAt="9:45 AM"
          tableName="Table 1"
          serverName="Sam"
          guestCount={2}
          taxRate={0.15}
          items={items}
          activeOrders={[]}
          onUpdateQuantity={(itemId, newQuantity) => {
            console.log(itemId, newQuantity) // Replace with state update logic
          }}
      />
    </div>
  );
}