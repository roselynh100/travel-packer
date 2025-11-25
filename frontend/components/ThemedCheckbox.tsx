import { ThemedText } from "@/components/ThemedText";
import { cn } from "@/helpers/cn";
import { Checkbox, CheckboxProps } from "expo-checkbox";
import { View } from "react-native";

export type ThemedCheckboxProps = CheckboxProps & {
  size?: "small" | "medium";
  label: string;
};

export function ThemedCheckbox({
  size = "small",
  value,
  onValueChange,
  label,
  className,
  ...rest
}: ThemedCheckboxProps) {
  const gap = size === "small" ? "gap-2" : "gap-4";

  const boxSize = size === "small" ? "w-4 h-4" : "w-6 h-6";

  const text = size === "small" ? "default" : "subtitle";

  return (
    <View className={cn("flex-row items-center", gap)}>
      <Checkbox
        value={value}
        onValueChange={onValueChange}
        className={cn(boxSize, className)}
        {...rest}
      />
      <ThemedText type={text}>{label}</ThemedText>
    </View>
  );
}
