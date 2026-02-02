export type User = {
  name: string;
  email: string;
  password: string; // TODO: how to safely save their password (this is a BE thing)
  age?: number;
  gender?: string;
  user_id?: string;
};

export enum Gender {
  male = "Male",
  female = "Female",
  non_binary = "Non-binary",
  other = "Other",
  prefer_not_to_disclose = "Prefer not to disclose",
}

export enum BagType {
  carry_on = "Carry-on",
  checked = "Checked",
}

export type Trip = {
  destination: string;
  duration_days: number;
  doing_laundry: boolean;
  airline: string;
  bag_type: string;
  activities?: string[];
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

export type PackingRecommendationStatus = "pack" | "remove" | "swap";

export type PackingRecommendation = {
  status: PackingRecommendationStatus;
  reason?: string;
  swap_candidates?: Item[];
};

export type ItemWithPackingRecommendation = Item & {
  item_name: string;
  packing_recommendation: PackingRecommendationStatus | null;
};

// Union type for packing list items
export type PackingListItem = RecommendedItem | ItemWithPackingRecommendation;
