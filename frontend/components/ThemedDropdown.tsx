import { useState } from "react";
import { Platform, ActionSheetIOS, Pressable, Text } from "react-native";
import DropDownPicker from "react-native-dropdown-picker";

export type ThemedDropdownProps<T extends string> = {
  value: T | null;
  onChange: (v: T) => void;
  options: T[];
};

export function ThemedDropdown<T extends string>({
  value,
  onChange,
  options,
}: ThemedDropdownProps<T>) {
  const [open, setOpen] = useState(false);

  const items = options.map((opt) => ({ label: opt, value: opt }));

  // Use native iOS ActionSheet
  if (Platform.OS === "ios") {
    const handlePress = () => {
      ActionSheetIOS.showActionSheetWithOptions(
        {
          options: ["Cancel", ...options],
          cancelButtonIndex: 0,
        },
        (buttonIndex) => {
          if (buttonIndex > 0) {
            onChange(options[buttonIndex - 1]);
          }
        }
      );
    };

    return (
      <Pressable
        onPress={handlePress}
        style={{
          borderRadius: 12,
          padding: 12,
          backgroundColor: "var(--color-bg-nav)",
          borderColor: "var(--color-text-placeholder)",
          borderWidth: 2,
          justifyContent: "center",
          minHeight: 48,
        }}
      >
        <Text
          style={{
            color: value
              ? "var(--color-text)"
              : "var(--color-text-placeholder)",
          }}
        >
          {value || "Select..."}
        </Text>
      </Pressable>
    );
  }

  // Use DropDownPicker for Android and Web
  return (
    <DropDownPicker
      open={open}
      value={value}
      items={items}
      setOpen={setOpen}
      setValue={(val) => onChange(val as unknown as T)}
      style={{
        borderRadius: 12,
        padding: 12,
        backgroundColor: "var(--color-bg-nav)",
        borderColor: "var(--color-text-placeholder)",
        borderWidth: 2,
      }}
      dropDownContainerStyle={{
        backgroundColor: "var(--color-bg-nav)",
        borderColor: "var(--color-text-placeholder)",
        borderLeftWidth: 2,
        borderRightWidth: 2,
        borderBottomWidth: 2,
      }}
      listItemContainerStyle={{
        backgroundColor: "var(--color-bg-nav)",
      }}
      textStyle={{
        color: "var(--color-text)",
      }}
      placeholder="Select..."
    />
  );
}
