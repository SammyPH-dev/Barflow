//Props for cards
export type DrinkCardProps = {
  name: string;
  description: string;
  imageUrl?: string;
  price?: number;
};

// Props for when clicking on a card (the popup)
export type DrinkDetailsProps = {
  name: string;
  description: string;
  onClose: () => void;
  imageUrl: string;
};

// One recommendation based on ingredient expiry.
export type ExpiringDrink = {
  recipe_id: number;
  name: string;
  reason: string;
};

// One recommendation based on sales.
export type PopularDrink = {
  recipe_id: number;
  name: string;
  quantity_ordered: number | null;
};

// The complete response from GET /api/v1/recommendations/drinks.
export type RecommendationsResponse = {
  expiring_drinks: ExpiringDrink[];
  popular_drinks: PopularDrink[];
};