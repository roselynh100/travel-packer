import { cn } from "@/helpers/cn";
import { useState } from "react";
import { Text, View } from "react-native";
import { Dropdown } from "react-native-element-dropdown";

type ThemedDropdownProps = {
  data: { label: string; value: string }[];
  value: string | null;
  onChange: (value: string) => void;
  placeholder?: string;
};

export function ThemedDropdown({
  data,
  value,
  onChange,
  placeholder = "Select item",
}: ThemedDropdownProps) {
  const [focused, setFocused] = useState(false);

  const ringColor = focused
    ? "border-[var(--color-primary)]"
    : "border-transparent";

  const renderItem = (item: { label: string; value: string }) => {
    const isSelected = value === item.value;
    return (
      <View
        className={cn(
          "p-3",
          isSelected ? "bg-teal-400/40" : "bg-[var(--color-bg-nav)]",
        )}
      >
        <Text className="text-[var(--color-text)]">{item.label}</Text>
      </View>
    );
  };

  return (
    <View className={cn("rounded-2xl border-2", ringColor)}>
      <Dropdown
        style={{
          borderRadius: 12,
          padding: 12,
          backgroundColor: "var(--color-bg-nav)",
          borderColor: "var(--color-text-placeholder)",
          borderWidth: 2,
        }}
        placeholderStyle={{
          color: "var(--color-text-placeholder)",
        }}
        data={data}
        renderItem={renderItem}
        maxHeight={300}
        labelField="label"
        valueField="value"
        placeholder={!focused ? placeholder : ""}
        value={value}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        onChange={(item) => {
          onChange(item.value);
        }}
      />
    </View>
  );
}
