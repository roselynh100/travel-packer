import { View } from "react-native";
import { ThemedText } from "@/components/ThemedText";
import { IconSymbol } from "@/components/ui/icon-symbol";

type PackingListPillProps = {
  type: "weight" | "volume";
  value: number;
};

// TODO: Convert to percentage of limit
export function PackingListPill({ type, value }: PackingListPillProps) {
  const color = value > 100 ? "red" : "green";

  const text =
    type === "weight" ? `Weight: ${value} kg` : `Volume: ${value} cm3`;

  return (
    <View
      className={`border-2 border-${color}-500 rounded-full px-4 py-2 flex-row gap-1 items-center`}
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
