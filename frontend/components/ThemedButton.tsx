import { cn } from "@/helpers/cn";
import { Pressable, Text, type PressableProps } from "react-native";

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
  const backgroundColor =
    variant === "solid" ? "bg-[var(--color-primary)]" : "bg-transparent";

  const textColor =
    variant === "solid" ? "text-white" : "text-[var(--color-primary)]"; // TODO: fix bg colour and then fix this to black?

  const border =
    variant === "outline"
      ? "border border-2 border-[var(--color-primary)]"
      : "";

  return (
    <Pressable
      className={cn(
        "rounded-full items-center justify-center py-3 active:opacity-80",
        backgroundColor,
        border,
        className
      )}
      {...rest}
    >
      <Text className={cn("font-medium text-lg", textColor)}>{title}</Text>
    </Pressable>
  );
}
