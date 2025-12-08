import { View } from "react-native";
import { ThemedText } from "@/components/ThemedText";
import { IconSymbol } from "@/components/ui/icon-symbol";

type PackingListPillProps = {
  type: "weight" | "volume";
  value: number;
};

// TODO: Convert to percentage of limit
export function PackingListPill({ type, value }: PackingListPillProps) {
  // TODO: Fix this logic
  const borderColor = value > 0 ? "border-yellow-500" : "border-green-500";

  const text =
    type === "weight"
      ? `Weight: ${value.toFixed(2)} kg`
      : `Volume: ${value.toFixed(2)} cm3`;

  return (
    <View
      className={`border-2 ${borderColor} rounded-full px-4 py-2 flex-row gap-1 items-center`}
    >
      <IconSymbol
        name={type === "weight" ? "gauge" : "cube.box.fill"}
        size={24}
        color="var(--color-text)"
      />
      <ThemedText className="text-sm">{text}</ThemedText>
    </View>
  );
}
