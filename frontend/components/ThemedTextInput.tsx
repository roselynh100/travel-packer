import { TextInput, type TextInputProps } from "react-native";

import { useThemeColor } from "@/hooks/use-theme-color";

export type ThemedTextInputProps = TextInputProps & {
  lightColor?: string;
  darkColor?: string;
};

export function ThemedTextInput({
  style,
  lightColor,
  darkColor,
  ...otherProps
}: ThemedTextInputProps) {
  const backgroundColor = useThemeColor(
    { light: lightColor, dark: darkColor },
    "background"
  );

  const borderColor = useThemeColor(
    { light: lightColor, dark: darkColor },
    "tabIconDefault"
  );

  const color = useThemeColor({ light: lightColor, dark: darkColor }, "text");

  const padding = 12;

  return (
    <TextInput
      style={[{ backgroundColor, borderColor, color, padding }, style]}
      placeholderTextColor={borderColor}
      {...otherProps}
    />
  );
}
