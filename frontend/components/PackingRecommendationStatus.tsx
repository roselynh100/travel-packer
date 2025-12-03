import { ThemedText } from "@/components/ThemedText";
import { PackingRecommendation } from "@/constants/types";

type PackingRecommendationStatusProps = {
  status: PackingRecommendation | null;
};

export function PackingRecommendationStatus({
  status,
}: PackingRecommendationStatusProps) {
  switch (status) {
    case "pack":
      return <ThemedText className="text-green-500">✅ PACK</ThemedText>;
    case "remove":
      return <ThemedText className="text-red-500">🚫 LEAVE</ThemedText>;
    case "swap":
      return <ThemedText className="text-yellow-500">⚠️ RECONSIDER</ThemedText>;
    default:
      return null;
  }
}
