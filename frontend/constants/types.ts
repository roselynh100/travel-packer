export type User = {
  name: string;
  email: string;
  password: string; // TODO: how to safely save their password (this is a BE thing)
  user_id?: string;
  // TODO: gender for user
};

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
