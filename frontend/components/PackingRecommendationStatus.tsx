import { ThemedText } from "@/components/ThemedText";
import { PackingRecommendationStatus as PackingRecommendationStatusType } from "@/constants/types";
import { useTheme } from "@/theme/useTheme";

type PackingRecommendationStatusProps = {
  status: PackingRecommendationStatusType | null;
};

export function PackingRecommendationStatus({
  status,
}: PackingRecommendationStatusProps) {
  const theme = useTheme();

  switch (status) {
    case "pack":
      return (
        <ThemedText style={{ color: theme.success.border }}>✅ PACK</ThemedText>
      );
    case "remove":
      return (
        <ThemedText style={{ color: theme.error.border }}>🚫 LEAVE</ThemedText>
      );
    case "swap":
      return (
        <ThemedText style={{ color: theme.warning.border }}>
          ⚠️ RECONSIDER
        </ThemedText>
      );
    default:
      return null;
  }
}
