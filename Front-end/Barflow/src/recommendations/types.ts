export type DrinkCardProps = {
  name: string;
  description: string;
  imageUrl: string;
  price: number;
};

export type DrinkDetailsProps = {
  name: string;
  description: string;
  onClose: () => void;
  imageUrl: string;
};

