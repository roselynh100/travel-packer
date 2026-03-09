import { ThemedText } from "@/components/ThemedText";
import { cn } from "@/helpers/cn";
import { useTheme } from "@/theme/useTheme";
import { Pressable, type PressableProps } from "react-native";

export type ThemedButtonProps = PressableProps & {
  variant?: "solid" | "outline";
  title: string;
};

export function ThemedButton({
  variant = "solid",
  title,
  className,
  ...rest
}: ThemedButtonProps) {
  const theme = useTheme();
  const isSolid = variant === "solid";

  return (
    <Pressable
      className={cn(
        "rounded-2xl items-center justify-center py-3 px-5 active:opacity-80 border-2",
        className,
      )}
      style={
        isSolid
          ? { backgroundColor: theme.primary, borderColor: theme.primary }
          : { backgroundColor: "transparent", borderColor: theme.primary }
      }
      {...rest}
    >
      <ThemedText style={{ color: isSolid ? "#ffffff" : theme.primary }}>
        {title}
      </ThemedText>
    </Pressable>
  );
}
