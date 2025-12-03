import { Pressable, View } from "react-native";
import { useState } from "react";
import { ThemedText } from "@/components/ThemedText";
import { RecommendedItem } from "@/constants/types";
import { ThemedCheckbox } from "@/components/ThemedCheckbox";
import { PackingRecommendationStatus } from "@/components/PackingRecommendationStatus";

type PackingListItemProps = {
  item: RecommendedItem;
  checked: boolean;
  onToggle: () => void;
};

export function PackingListItem({
  item,
  checked,
  onToggle,
}: PackingListItemProps) {
  const [expanded, setExpanded] = useState(false);

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
          />
          <PackingRecommendationStatus status="remove" />
        </View>

        {expanded && (
          <View className="mt-2 pl-6 gap-1">
            {item.reason && (
              <ThemedText className="text-gray-500">{item.reason}</ThemedText>
            )}
            {item.priority && (
              <ThemedText className="text-gray-500">
                Priority: {item.priority}
              </ThemedText>
            )}
          </View>
        )}
      </View>
    </Pressable>
  );
}
