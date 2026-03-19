import { Modal, View } from "react-native";

import { ThemedButton } from "@/components/ThemedButton";
import { ThemedText } from "@/components/ThemedText";
import { ModalCloseButton } from "@/components/ModalCloseButton";
import { useTheme } from "@/theme/useTheme";
import type { ItemWithPackingRecommendation } from "@/constants/types";

type PackingRecommendationModalProps = {
  visible: boolean;
  item: ItemWithPackingRecommendation | null;
  onSecondary: () => void;
  onPrimary: () => void;
};

export function PackingRecommendationModal({
  visible,
  item,
  onSecondary,
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

  const swapCandidates = recommendation?.swap_candidates ?? [];

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onSecondary}
    >
      <View className="flex-1 justify-center items-center bg-black/70 px-6">
        <View
          className="rounded-2xl pt-16 pb-12 px-8 w-full max-w-md"
          style={{ backgroundColor: theme.bgNav }}
        >
          <ModalCloseButton onPress={onSecondary} />
          <ThemedText type="subtitle" className="text-center mb-3">
            {title}
          </ThemedText>
          {recommendation?.reason && (
            <ThemedText className="text-center mb-2">
              {recommendation.reason}
            </ThemedText>
          )}
          {swapCandidates.length > 0 && (
            <View className="my-2">
              <ThemedText type="defaultSemiBold" className="mb-1">
                To bring your {item?.item_name}, you should remove:
              </ThemedText>
              {swapCandidates.map((c) => (
                <ThemedText key={c.item_id}>
                  • {c.cv_result?.item_name ?? "—"}
                </ThemedText>
              ))}
            </View>
          )}
          <View className="w-full gap-3 mt-4">
            <ThemedButton
              title="Pack anyway"
              variant="outline"
              onPress={onSecondary}
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
