import { Platform, Pressable, View } from "react-native";
import { useState } from "react";
import { ThemedText } from "@/components/ThemedText";
import { ItemWithPackingRecommendation } from "@/constants/types";
import { ThemedCheckbox } from "@/components/ThemedCheckbox";
import { PackingRecommendationStatus } from "@/components/packing";
import { cn } from "@/helpers/cn";
import { useTheme } from "@/theme/useTheme";

type PackingListItemProps = {
  item: ItemWithPackingRecommendation;
  checked: boolean;
  onToggle: () => void;
  onPressRecommendation?: (item: ItemWithPackingRecommendation) => void;
};

export function PackingListItem({
  item,
  checked,
  onToggle,
  onPressRecommendation,
}: PackingListItemProps) {
  const theme = useTheme();
  const [expanded, setExpanded] = useState(false);

  const recommendation =
    "packing_recommendation" in item ? item.packing_recommendation : null;

  const canOpenRecommendation =
    recommendation &&
    (recommendation.status === "remove" || recommendation.status === "swap");

  // ASSUMPTION: Priority is an internal value (should not be shown to user)
  // Disabled checkbox if packing recommendation is not available ("item" is not an Item in backend)
  return (
    <Pressable
      onPress={() => setExpanded((prev) => !prev)}
      style={({ pressed }) => ({
        padding: 8,
        backgroundColor: pressed ? theme.bgNav : "transparent",
        borderBottomWidth: 1,
        borderBottomColor: theme.textPlaceholder,
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
            status={recommendation?.status ?? null}
            onPress={
              canOpenRecommendation && onPressRecommendation
                ? () =>
                    onPressRecommendation(item as ItemWithPackingRecommendation)
                : undefined
            }
          />
        </View>

        {expanded && "packing_recommendation" in item && (
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
  );
}
