export type Trip = {
  destination: string;
  duration_days: number;
  doing_laundry: boolean;
  activities?: string;
  trip_id?: string;
};

export type RecommendedItem = {
  item_name: string;
  reason?: string;
  priority?: number;
};
