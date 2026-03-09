import type { ReactNode } from "react";
import {
  Platform,
  ScrollView,
  type ScrollViewProps,
  type ViewStyle,
} from "react-native";
import { useTheme } from "@/theme/useTheme";
import { cn } from "@/helpers/cn";

type ScreenScrollProps = Omit<ScrollViewProps, "contentContainerStyle"> & {
  children: ReactNode;
  contentContainerStyle?: ViewStyle | ViewStyle[];
  /**
   * Some screens want content spaced out vertically (e.g. footer button).
   */
  variant?: "default" | "spaceBetween";
};

export function ScreenScroll({
  children,
  className,
  style,
  contentContainerStyle,
  variant = "default",
  keyboardShouldPersistTaps = "handled",
  showsVerticalScrollIndicator = false,
  ...rest
}: ScreenScrollProps) {
  const theme = useTheme();

  const baseContent: ViewStyle = {
    flexGrow: 1,
    ...(variant === "spaceBetween"
      ? { justifyContent: "space-between" }
      : null),
  };

  return (
    <ScrollView
      className={cn(
        "flex-1",
        Platform.OS === "web" ? "p-12" : "p-6",
        className,
      )}
      style={[{ backgroundColor: theme.bg }, style]}
      contentContainerStyle={[baseContent, contentContainerStyle]}
      keyboardShouldPersistTaps={keyboardShouldPersistTaps}
      showsVerticalScrollIndicator={showsVerticalScrollIndicator}
      {...rest}
    >
      {children}
    </ScrollView>
  );
}
