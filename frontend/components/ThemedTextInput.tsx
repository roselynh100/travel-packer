import {
  INPUT_BORDER_RADIUS,
  INPUT_FONT_FAMILY,
  INPUT_FONT_SIZE,
  INPUT_MIN_HEIGHT,
  INPUT_PADDING,
} from "@/theme/inputStyles";
import { useTheme } from "@/theme/useTheme";
import { useState } from "react";
import { TextInput, View, type TextInputProps } from "react-native";

export function ThemedTextInput({ style, ...otherProps }: TextInputProps) {
  const theme = useTheme();
  const [focused, setFocused] = useState(false);

  return (
    <View
      className="rounded-2xl border-2"
      style={{
        borderColor: focused ? theme.primary : "transparent",
        overflow: "hidden",
      }}
    >
      <TextInput
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        className="rounded-xl border-2"
        style={[
          {
            backgroundColor: theme.bgNav,
            color: theme.text,
            borderColor: theme.textPlaceholder,
            paddingHorizontal: INPUT_PADDING,
            paddingVertical: INPUT_PADDING,
            minHeight: INPUT_MIN_HEIGHT,
            fontSize: INPUT_FONT_SIZE,
            fontFamily: INPUT_FONT_FAMILY,
            borderRadius: INPUT_BORDER_RADIUS,
          },
          style,
        ]}
        placeholderTextColor={theme.textPlaceholder}
        {...otherProps}
      />
    </View>
  );
}
