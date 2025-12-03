import { ThemedText } from "@/components/ThemedText";

type PackingRecommendationStatusProps = {
  status: "pack" | "remove" | "swap";
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
