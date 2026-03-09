import {
  INPUT_BORDER_RADIUS,
  INPUT_FONT_FAMILY,
  INPUT_FONT_SIZE,
  INPUT_MIN_HEIGHT,
  INPUT_PADDING,
} from "@/theme/inputStyles";
import { ThemedText } from "@/components/ThemedText";
import { useTheme } from "@/theme/useTheme";
import { useState } from "react";
import { View } from "react-native";
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
  const theme = useTheme();
  const [focused, setFocused] = useState(false);

  const renderItem = (item: { label: string; value: string }) => {
    const isSelected = value === item.value;
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
        <Dropdown
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
    </View>
  );
}
