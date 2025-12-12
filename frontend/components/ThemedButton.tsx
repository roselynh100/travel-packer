import { ThemedText } from "@/components/ThemedText";
import { cn } from "@/helpers/cn";
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
  const backgroundColor =
    variant === "solid" ? "bg-[var(--color-primary)]" : "bg-transparent";

  const textColor =
    variant === "solid" ? "text-white" : "text-[var(--color-primary)]"; // TODO: fix bg colour and then fix this to black?

  const border =
    variant === "outline"
      ? "border-[var(--color-primary)]"
      : "border-transparent";

  return (
    <Pressable
      className={cn(
        "rounded-full items-center justify-center py-3 px-5 active:opacity-80 border-2",
        backgroundColor,
        border,
        className
      )}
      {...rest}
    >
      <ThemedText className={textColor}>{title}</ThemedText>
    </Pressable>
  );
}
