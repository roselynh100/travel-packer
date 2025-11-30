import { cn } from "@/helpers/cn";
import { useState } from "react";
import { TextInput, View, type TextInputProps } from "react-native";

export function ThemedTextInput({ style, ...otherProps }: TextInputProps) {
  const [focused, setFocused] = useState(false);

  const ringColor = focused
    ? "border-[var(--color-primary)]"
    : "border-transparent";

  const backgroundColor = "bg-[var(--color-bg-nav)]";

  const text = "text-[var(--color-text)]";

  const border = "border-2 border-[var(--color-text-placeholder)]";

  return (
    <View className={cn("rounded-2xl border-2", ringColor)}>
      <TextInput
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        className={cn("p-3 rounded-xl", backgroundColor, text, border)}
        placeholderTextColor="var(--color-text-placeholder)"
        {...otherProps}
      />
    </View>
  );
}
