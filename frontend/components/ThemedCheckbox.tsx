import { Pressable, View } from "react-native";
import { Checkbox, CheckboxProps } from "expo-checkbox";
import { ThemedText } from "@/components/ThemedText";
import { cn } from "@/helpers/cn";
import { useTheme } from "@/theme/useTheme";

export type ThemedCheckboxProps = CheckboxProps & {
  size?: "small" | "medium";
  label: string;
  accessory?: React.ReactNode;
};

export function ThemedCheckbox({
  size = "small",
  value,
  onValueChange,
  label,
  accessory,
  className,
  ...rest
}: ThemedCheckboxProps) {
  const theme = useTheme();

  const gap = size === "small" ? "gap-2" : "gap-4";
  const boxSize = size === "small" ? "w-4 h-4" : "w-6 h-6";
  const text = size === "small" ? "default" : "subtitle";

  return (
    <View className={cn("flex-row items-center", gap)}>
      <Pressable
        onPress={(e) => {
          e.stopPropagation();
        }}
      >
        <Checkbox
          value={value}
          onValueChange={onValueChange}
          color={theme.primary}
          className={cn(boxSize, className)}
          {...rest}
        />
      </Pressable>
      {accessory}
      <ThemedText type={text}>{label}</ThemedText>
    </View>
  );
}
