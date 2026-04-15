import { Pressable } from "react-native";
import { ThemedText } from "@/components/ThemedText";
import { PackingRecommendationStatus as PackingRecommendationStatusType } from "@/constants/types";
import { useTheme } from "@/theme/useTheme";

type PackingRecommendationStatusProps = {
  status: PackingRecommendationStatusType | null;
  onPress?: () => void;
};

export function PackingRecommendationStatus({
  status,
  onPress,
}: PackingRecommendationStatusProps) {
  const theme = useTheme();

  switch (status) {
    case "pack":
      return null;
    case "remove":
      return (
        <Pressable onPress={onPress} hitSlop={8}>
          <ThemedText
            className="rounded-2xl px-3 py-0.5"
            style={{
              borderColor: theme.error.border,
              backgroundColor: theme.error.bg,
              borderWidth: 2,
              fontSize: 14,
            }}
          >
            🚫 LEAVE
          </ThemedText>
        </Pressable>
      );
    case "swap":
      return (
        <Pressable onPress={onPress} hitSlop={8}>
          <ThemedText
            className="rounded-2xl px-3 py-0.5"
            style={{
              borderColor: theme.warning.border,
              backgroundColor: theme.warning.bg,
              borderWidth: 2,
              fontSize: 14,
            }}
          >
            ⚠️ RECONSIDER
          </ThemedText>
        </Pressable>
      );
  }
}
