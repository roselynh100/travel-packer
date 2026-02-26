import { cn } from "@/helpers/cn";
import React, { useState } from "react";
import { View, Text, TouchableOpacity } from "react-native";
import { MultiSelect } from "react-native-element-dropdown";

type ThemedMultiSelectProps = {
  data: { label: string; value: string }[];
  value: string[];
  onChange: (value: string[]) => void;
  placeholder?: string;
  searchPlaceholder?: string;
};

export const ThemedMultiSelect = ({
  data,
  value,
  onChange,
  placeholder = "Select item",
  searchPlaceholder = "Search...",
}: ThemedMultiSelectProps) => {
  const [focused, setFocused] = useState(false);

  const ringColor = focused
    ? "border-[var(--color-primary)]"
    : "border-transparent";

  const renderItem = (item: { label: string; value: string }) => {
    const isSelected = value.includes(item.value);
    return (
      <View className={cn("p-3", isSelected ? "bg-teal-400/40" : "bg-white")}>
        <Text className="text-[var(--color-text)]">{item.label}</Text>
      </View>
    );
  };

  const renderSelectedItem = (
    item: { label: string; value: string },
    unSelect?: (item: { label: string; value: string }) => void,
  ) => {
    return (
      <TouchableOpacity
        onPress={() => unSelect && unSelect(item)}
        className="mr-2"
      >
        <View className="flex-row items-center px-3 py-1.5 rounded-full bg-teal-400/20 border border-[var(--color-primary)]">
          <Text className="text-[var(--color-text)] mr-2">{item.label}</Text>
          <Text className="text-[var(--color-primary)] font-bold">×</Text>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <View className={cn("rounded-2xl border-2", ringColor)}>
      <View className="rounded-xl border-2 border-[var(--color-text-placeholder)] bg-[var(--color-bg-nav)]">
        <MultiSelect
          style={{
            borderRadius: 12,
            padding: 12,
          }}
          placeholderStyle={{
            color: "var(--color-text-placeholder)",
          }}
          data={data}
          renderItem={renderItem}
          renderSelectedItem={renderSelectedItem}
          search
          maxHeight={300}
          labelField="label"
          valueField="value"
          placeholder={!focused ? placeholder : ""}
          searchPlaceholder={searchPlaceholder}
          value={value}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          onChange={(item) => {
            onChange(item);
          }}
          inside
        />
      </View>
    </View>
  );
};
