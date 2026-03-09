import { Modal, View } from "react-native";
import { ThemedButton } from "@/components/ThemedButton";
import { ThemedText } from "@/components/ThemedText";
import { useTheme } from "@/theme/useTheme";

type PackingRecommendationVariant = "remove" | "swap" | null;

type PackingRecommendationModalProps = {
  visible: boolean;
  variant: PackingRecommendationVariant;
  itemName?: string;
  onIgnore: () => void;
  onPrimary: () => void;
};

export function PackingRecommendationModal({
  visible,
  variant,
  itemName,
  onIgnore,
  onPrimary,
}: PackingRecommendationModalProps) {
  const theme = useTheme();

  if (!variant) {
    return null;
  }

  const isRemove = variant === "remove";

  const title = isRemove
    ? "Your item should be left behind"
    : "Your item should be swapped";

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
          className="rounded-2xl pt-18 pb-12 px-8 w-full max-w-md"
          style={{ backgroundColor: theme.bgNav }}
        >
          <ThemedText type="subtitle" className="text-center mb-3">
            {title}
          </ThemedText>
          {itemName && (
            <ThemedText className="text-center mb-2">
              Item: {itemName}
            </ThemedText>
          )}
          <View className="w-full gap-3">
            <ThemedButton
              title="Ignore"
              variant="outline"
              onPress={onIgnore}
              className="w-full"
            />
            <ThemedButton
              title={primaryLabel}
              onPress={onPrimary}
              className="w-full"
            />
          </View>
        </View>
      </View>
    </Modal>
  );
}
