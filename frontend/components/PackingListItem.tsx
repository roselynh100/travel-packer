import { useState } from "react";
import { Pressable, View } from "react-native";

import { ThemedText } from "@/components/ThemedText";
import { PackingListItem as PackingListItemType } from "@/constants/types";
import { ThemedCheckbox } from "@/components/ThemedCheckbox";
import { PackingRecommendationStatus } from "@/components/PackingRecommendationStatus";
import { useTheme } from "@/theme/useTheme";
import { QuantityModal } from "@/components/QuantityModal";
import { patchItemQuantity } from "@/api/items";

type PackingListItemProps = {
  item: PackingListItemType;
  checked: boolean;
  onToggle: () => void;
  onQuantityUpdated?: (itemId: string, quantity: number) => void;
};

export function PackingListItem({
  item,
  checked,
  onToggle,
  onQuantityUpdated,
}: PackingListItemProps) {
  const theme = useTheme();
  const [expanded, setExpanded] = useState(false);
  const [quantityModalVisible, setQuantityModalVisible] = useState(false);
  const [isSavingQuantity, setIsSavingQuantity] = useState(false);

  const itemId = "item_id" in item ? item.item_id : null;
  const quantity = "quantity" in item ? (item.quantity ?? 1) : 1;

  const handleConfirmQuantity = async (nextQuantity: number) => {
    if (!itemId) return;
    setIsSavingQuantity(true);
    try {
      await patchItemQuantity(itemId, nextQuantity);
      onQuantityUpdated?.(itemId, nextQuantity);
      setQuantityModalVisible(false);
    } finally {
      setIsSavingQuantity(false);
    }
  };

  // ASSUMPTION: Priority is an internal value (should not be shown to user)
  // Disabled checkbox if packing recommendation is not available ("item" is not an Item in backend)
  return (
    <Pressable
      onPress={() => setExpanded((prev) => !prev)}
      style={({ pressed }) => ({
        padding: 8,
        backgroundColor: pressed ? theme.bgNav : "transparent",
      })}
    >
      <View className="flex-col">
        <View className="flex-row items-center gap-4">
          <ThemedCheckbox
            label={item.item_name}
            value={checked}
            onValueChange={onToggle}
            disabled={!("packing_recommendation" in item)}
          />

          {itemId && (
            <Pressable
              onPress={(e) => {
                e.stopPropagation();
                if (!isSavingQuantity) setQuantityModalVisible(true);
              }}
              style={({ pressed }) => ({
                opacity: isSavingQuantity ? 0.5 : pressed ? 0.7 : 1,
              })}
            >
              <View
                className="px-3 py-1 rounded-full"
                style={{ backgroundColor: theme.bgNav }}
              >
                <ThemedText className="text-gray-500">x{quantity}</ThemedText>
              </View>
            </Pressable>
          )}

          <PackingRecommendationStatus
            status={
              "packing_recommendation" in item
                ? item.packing_recommendation
                : null
            }
          />
        </View>

        {expanded && (
          <View className="mt-2 pl-6 gap-1">
            {"reason" in item && (
              <ThemedText className="text-gray-500">{item.reason}</ThemedText>
            )}

            {"weight_kg" in item && item.weight_kg !== null && (
              <ThemedText className="text-gray-500">
                Weight: {item.weight_kg.toFixed(2)} kg
              </ThemedText>
            )}

            {"estimated_volume_cm3" in item &&
              item.estimated_volume_cm3 !== null && (
                <ThemedText className="text-gray-500">
                  Volume: {item.estimated_volume_cm3.toFixed(2)} cm³
                </ThemedText>
              )}
          </View>
        )}
      </View>

      {itemId && (
        <QuantityModal
          visible={quantityModalVisible}
          itemName={item.item_name}
          initialQuantity={quantity}
          onCancel={() => setQuantityModalVisible(false)}
          onConfirm={handleConfirmQuantity}
        />
      )}
    </Pressable>
  );
}
