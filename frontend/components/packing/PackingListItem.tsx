import { useState } from "react";
import { Platform, Pressable, View } from "react-native";

import { ThemedText } from "@/components/ThemedText";
import { ItemWithPackingRecommendation } from "@/constants/types";
import { ThemedCheckbox } from "@/components/ThemedCheckbox";
import { PackingRecommendationStatus } from "@/components/packing";
import { PackingThumbnail } from "@/components/packing/PackingThumbnail";
import { cn } from "@/helpers/cn";
import { useTheme } from "@/theme/useTheme";

type PackingListItemProps = {
  item: ItemWithPackingRecommendation;
  checked: boolean;
  onToggle: () => void;
  onPressRecommendation: (item: ItemWithPackingRecommendation) => void;
  recommendationDismissed: boolean;
  onQuantityUpdated: (itemId: string, quantity: number) => void;
};

export function PackingListItem({
  item,
  checked,
  onToggle,
  onPressRecommendation,
  recommendationDismissed,
  onQuantityUpdated,
}: PackingListItemProps) {
  const theme = useTheme();
  const [expanded, setExpanded] = useState(false);

  const recommendation = item.packing_recommendation;
  const shouldShowRecommendation = recommendation && !recommendationDismissed;
  const canOpenRecommendation =
    shouldShowRecommendation &&
    (recommendation.status === "remove" || recommendation.status === "swap");

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
    <>
      <Pressable
        onPress={() => setExpanded((prev) => !prev)}
        style={({ pressed }) => ({
          paddingTop: 12,
          paddingBottom: 12,
          backgroundColor: pressed ? theme.bgNav : "transparent",
          borderBottomWidth: 1,
          borderBottomColor: theme.textPlaceholder,
        })}
      >
        <View className="flex-col">
          <View className="flex-row items-center justify-between">
            <View className="flex-row items-center gap-3">
              <ThemedCheckbox
                label={item.item_name}
                value={checked}
                onValueChange={onToggle}
                accessory={<PackingThumbnail photoUri={item.photo_uri} />}
              />
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

          {expanded && (
            <View
              className={cn(
                "mt-2 flex-col gap-1",
                Platform.OS === "web" ? "pl-6" : "pl-8",
              )}
            >
              {item.weight_kg && (
                <ThemedText>Weight: {item.weight_kg.toFixed(2)} kg</ThemedText>
              )}
              {item.estimated_volume_cm3 && (
                <ThemedText>
                  Volume: {item.estimated_volume_cm3.toFixed(2)} cm³
                </ThemedText>
              )}
            </View>
          )}
        </View>
      </Pressable>
    </>
  );
}
