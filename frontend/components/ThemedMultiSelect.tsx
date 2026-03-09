import {
  INPUT_BORDER_RADIUS,
  INPUT_FONT_FAMILY,
  INPUT_FONT_SIZE,
  INPUT_MIN_HEIGHT,
  INPUT_PADDING,
} from "@/theme/inputStyles";
import { ThemedText } from "@/components/ThemedText";
import { useTheme } from "@/theme/useTheme";
import React, { useState } from "react";
import { View, TouchableOpacity } from "react-native";
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
  const theme = useTheme();
  const [focused, setFocused] = useState(false);

  const renderItem = (item: { label: string; value: string }) => {
    const isSelected = value.includes(item.value);
    return (
      <View
        className="border-b"
        style={{
          padding: INPUT_PADDING,
          backgroundColor: isSelected ? theme.selectedItemBg : theme.bgNav,
          borderBottomColor: theme.textPlaceholder,
        }}
      >
        <ThemedText>{item.label}</ThemedText>
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
        <View
          className="flex-row items-center px-3 py-1.5 rounded-full bg-teal-400/20 border"
          style={{ borderColor: theme.primary }}
        >
          <ThemedText className="mr-2">{item.label}</ThemedText>
          <ThemedText style={{ color: theme.primary, fontWeight: "bold" }}>
            ×
          </ThemedText>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <View
      className="rounded-2xl border-2"
      style={{
        borderColor: focused ? theme.primary : "transparent",
        overflow: "hidden",
      }}
    >
      <View
        className="rounded-xl border-2"
        style={{
          borderColor: theme.textPlaceholder,
          backgroundColor: theme.bgNav,
          overflow: "hidden",
        }}
      >
        <MultiSelect
          style={{
            borderRadius: INPUT_BORDER_RADIUS,
            padding: INPUT_PADDING,
            minHeight: INPUT_MIN_HEIGHT,
            backgroundColor: theme.bgNav,
          }}
          placeholderStyle={{
            color: theme.textPlaceholder,
            fontSize: INPUT_FONT_SIZE,
            fontFamily: INPUT_FONT_FAMILY,
          }}
          selectedTextStyle={{
            color: theme.text,
            fontSize: INPUT_FONT_SIZE,
            fontFamily: INPUT_FONT_FAMILY,
          }}
          containerStyle={{
            backgroundColor: theme.bgNav,
            borderColor: theme.textPlaceholder,
            borderWidth: 1,
            borderRadius: INPUT_BORDER_RADIUS,
            overflow: "hidden",
          }}
          itemTextStyle={{
            color: theme.text,
            fontSize: INPUT_FONT_SIZE,
            fontFamily: INPUT_FONT_FAMILY,
          }}
          activeColor={theme.selectedItemBg}
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
