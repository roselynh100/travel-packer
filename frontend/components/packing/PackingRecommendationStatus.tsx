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
        <ThemedText
          className="rounded-2xl px-3 py-1"
          style={{
            borderColor: theme.success.border,
            backgroundColor: theme.success.bg,
            borderWidth: 2,
            fontSize: 14,
          }}
        >
          ✅ PACK
        </ThemedText>
      );
    case "remove":
      return (
        <ThemedText
          className="rounded-2xl px-3 py-1"
          style={{
            borderColor: theme.error.border,
            backgroundColor: theme.error.bg,
            borderWidth: 2,
            fontSize: 14,
          }}
        >
          🚫 LEAVE
        </ThemedText>
      );
    case "swap":
      return (
        <ThemedText
          className="rounded-2xl px-3 py-1"
          style={{
            borderColor: theme.warning.border,
            backgroundColor: theme.warning.bg,
            borderWidth: 2,
            fontSize: 14,
          }}
        >
          ⚠️ RECONSIDER
        </ThemedText>
      );
    default:
      return null;
  }
}
