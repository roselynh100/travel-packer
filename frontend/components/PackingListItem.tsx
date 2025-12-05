import { Pressable, View } from "react-native";
import { useState } from "react";
import { ThemedText } from "@/components/ThemedText";
import { PackingListItem as PackingListItemType } from "@/constants/types";
import { ThemedCheckbox } from "@/components/ThemedCheckbox";
import { PackingRecommendationStatus } from "@/components/PackingRecommendationStatus";

type PackingListItemProps = {
  item: PackingListItemType;
  checked: boolean;
  onToggle: () => void;
};

export function PackingListItem({
  item,
  checked,
  onToggle,
}: PackingListItemProps) {
  const [expanded, setExpanded] = useState(false);

  // ASSUMPTION: Priority is an internal value (should not be shown to user)
  // Disabled checkbox if packing recommendation is not available ("item" is not an Item in backend)
  return (
    <Pressable
      onPress={() => setExpanded((prev) => !prev)}
      style={({ pressed }) => ({
        padding: 8,
        backgroundColor: pressed ? "var(--color-bg-nav)" : "transparent",
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
    </Pressable>
  );
}
