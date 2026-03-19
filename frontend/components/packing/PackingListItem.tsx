import { Pressable, View } from "react-native";

import { ThemedText } from "@/components/ThemedText";
import { ItemWithPackingRecommendation } from "@/constants/types";
import { ThemedCheckbox } from "@/components/ThemedCheckbox";
import { PackingRecommendationStatus } from "@/components/packing";
import { PackingThumbnail } from "@/components/packing/PackingThumbnail";
import { useTheme } from "@/theme/useTheme";
import { formatItemName } from "@/helpers/formatItemName";

type PackingListItemProps = {
  item: ItemWithPackingRecommendation;
  checked: boolean;
  onToggle: () => void;
  onPressRecommendation: (item: ItemWithPackingRecommendation) => void;
  onQuantityUpdated: (itemId: string, quantity: number) => void;
};

export function PackingListItem({
  item,
  checked,
  onToggle,
  onPressRecommendation,
  onQuantityUpdated,
}: PackingListItemProps) {
  const theme = useTheme();

  const recommendation = item.packing_recommendation;
  const shouldShowRecommendation =
    recommendation &&
    !recommendation.is_accepted &&
    (recommendation.status === "remove" || recommendation.status === "swap");
  const canOpenRecommendation = shouldShowRecommendation;

  const quantity = item.quantity ?? 1;

  const canDecrement = quantity > 1;
  const canIncrement = quantity < 99;

  const changeQuantity = (delta: number) => {
    const nextQuantity = Math.min(99, Math.max(1, quantity + delta));
    if (nextQuantity === quantity) return;
    onQuantityUpdated(item.item_id, nextQuantity);
  };

  // ASSUMPTION: Priority is an internal value (should not be shown to user)
  // Disabled checkbox if packing recommendation is not available ("item" is not an Item in backend)
  return (
    <View
      className="py-4 border-b"
      style={{ borderColor: theme.textPlaceholder }}
    >
      <View className="flex-row items-center justify-between">
        <View className="flex-row items-center gap-3 flex-1">
          <ThemedCheckbox
            value={checked}
            onValueChange={onToggle}
            accessory={<PackingThumbnail photoUri={item.photo_uri} />}
          />
          <View className="flex-1">
            <View className="flex-row items-center gap-2">
              <ThemedText numberOfLines={1} className="flex-shrink">
                {formatItemName(item.item_name)}
              </ThemedText>
              {shouldShowRecommendation && (
                <PackingRecommendationStatus
                  status={recommendation.status}
                  onPress={
                    canOpenRecommendation
                      ? () => onPressRecommendation(item)
                      : undefined
                  }
                />
              )}
            </View>
            {(item.weight_kg || item.estimated_volume_cm3) && (
              <View className="flex-col gap-1">
                {item.weight_kg && (
                  <ThemedText className="text-xs">
                    Weight: {item.weight_kg.toFixed(2)} kg
                  </ThemedText>
                )}
                {item.estimated_volume_cm3 && (
                  <ThemedText className="text-xs">
                    Volume: {item.estimated_volume_cm3.toFixed(2)} cm³
                  </ThemedText>
                )}
              </View>
            )}
          </View>
        </View>
        <View className="flex-row items-center">
          <Pressable
            onPress={(e) => {
              e.stopPropagation();
              if (canDecrement) changeQuantity(-1);
            }}
            disabled={!canDecrement}
            style={({ pressed }) => ({
              opacity: !canDecrement ? 0.4 : pressed ? 0.7 : 1,
            })}
          >
            <View
              className="px-3 py-1 rounded-full"
              style={{ backgroundColor: theme.bg }}
            >
              <ThemedText type="defaultSemiBold">−</ThemedText>
            </View>
          </Pressable>
          <ThemedText className="mx-2 text-gray-700">{quantity}</ThemedText>
          <Pressable
            onPress={(e) => {
              e.stopPropagation();
              if (canIncrement) changeQuantity(1);
            }}
            disabled={!canIncrement}
            style={({ pressed }) => ({
              opacity: !canIncrement ? 0.4 : pressed ? 0.7 : 1,
            })}
          >
            <View
              className="px-3 py-1 rounded-full"
              style={{ backgroundColor: theme.bg }}
            >
              <ThemedText type="defaultSemiBold">+</ThemedText>
            </View>
          </Pressable>
        </View>
      </View>
    </View>
  );
}
