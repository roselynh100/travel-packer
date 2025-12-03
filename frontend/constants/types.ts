export type User = {
  name: string;
  email: string;
  password: string; // TODO: how to safely save their password (this is a BE thing)
  age?: number;
  gender?: Gender;
  user_id?: string;
};

export enum Gender {
  Male = "male",
  Female = "female",
  NonBinary = "non-binary",
  Other = "other",
  PrefNotToDisclose = "prefer not to disclose",
}

export type Trip = {
  destination: string;
  duration_days: number;
  doing_laundry: boolean;
  activities?: string;
  trip_id?: string;
  total_items_weight?: number;
  total_items_volume?: number;
};

export type RecommendedItem = {
  item_name: string;
  reason?: string;
  priority?: number;
};

export type Item = {
  item_id: string;
  item_importance: number;
  estimated_volume_cm3: number | null;
  weight_kg: number | null;
  cv_result: CVResult;
  trips: string[];
};

export type CVResult = {
  item_name: string;
  class_name: string;
  confidence_score: number;
  bounding_boxes: BoundingBox[];
  dimensions: Dimensions;
};

export type BoundingBox = {
  x_min: number;
  y_min: number;
  x_max: number;
  y_max: number;
};

export type Dimensions = {
  length: number;
  width: number;
  height: number | null;
};

export type PackingRecommendation = "pack" | "remove" | "swap";

// Union type for packing list items
export type PackingListItem =
  | RecommendedItem
  | (Item & { packing_recommendation: PackingRecommendation });
