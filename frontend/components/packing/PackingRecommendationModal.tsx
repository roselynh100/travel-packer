import { Modal, View } from "react-native";

import { ThemedButton } from "@/components/ThemedButton";
import { ThemedText } from "@/components/ThemedText";
import { useTheme } from "@/theme/useTheme";
import type { ItemWithPackingRecommendation } from "@/constants/types";

type PackingRecommendationModalProps = {
  visible: boolean;
  item: ItemWithPackingRecommendation | null;
  onIgnore: () => void;
  onPrimary: () => void;
};

export function PackingRecommendationModal({
  visible,
  item,
  onIgnore,
  onPrimary,
}: PackingRecommendationModalProps) {
  const theme = useTheme();

  const recommendation = item?.packing_recommendation ?? null;
  const variant =
    recommendation?.status === "remove" || recommendation?.status === "swap"
      ? recommendation.status
      : null;

  // Don't show modal for "pack" recommendation
  if (!variant) return null;

  const isRemove = variant === "remove";

  const title = isRemove
    ? `Your ${item?.item_name} should be left behind`
    : `Your ${item?.item_name} should be swapped`;

  const primaryLabel = isRemove ? "Remove" : "Swap";

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onIgnore}
    >
      <View className="flex-1 justify-center items-center bg-black/70 px-6">
        <View
          className="rounded-2xl pt-16 pb-12 px-8 w-full max-w-md"
          style={{ backgroundColor: theme.bgNav }}
        >
          <ThemedText type="subtitle" className="text-center mb-3">
            {title}
          </ThemedText>
          {recommendation?.reason && (
            <ThemedText className="text-center mb-2">
              {recommendation.reason}
            </ThemedText>
          )}
          <View className="w-full gap-3 mt-4">
            <ThemedButton
              title="Ignore"
              variant="outline"
              onPress={onIgnore}
              className="w-full"
            />
            <ThemedButton
              title={variant === "remove" ? "Remove" : "Swap"}
              onPress={onPrimary}
              className="w-full"
            />
          </View>
        </View>
      </View>
    </Modal>
  );
}
