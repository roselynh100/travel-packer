import { Pressable, View } from "react-native";
import { ThemedText } from "@/components/ThemedText";
import { useTheme } from "@/theme/useTheme";

export type ThemedBannerType = "success" | "warning" | "error";

export type ThemedBannerProps = {
  message: string;
  type: ThemedBannerType;
  /**
   * Optional action button on the right. If not provided, the button is hidden.
   */
  actionLabel?: string;
  onActionPress?: () => void;
};

export function ThemedBanner({
  message,
  type,
  actionLabel = "Dismiss",
  onActionPress,
}: ThemedBannerProps) {
  const theme = useTheme();

  let bg: string;
  let border: string;

  switch (type) {
    case "success":
      ({ bg, border } = theme.success);
      break;
    case "warning":
      ({ bg, border } = theme.warning);
      break;
    case "error":
      ({ bg, border } = theme.error);
      break;
    default:
      bg = theme.selectedItemBg;
      border = theme.primary;
      break;
  }

  return (
    <View
      className="w-full px-4 py-3 flex-row items-center"
      style={{
        backgroundColor: bg,
        borderWidth: 2,
        borderColor: border,
      }}
    >
      <ThemedText className="flex-1">{message}</ThemedText>
      {onActionPress && (
        <Pressable
          onPress={onActionPress}
          style={{
            paddingHorizontal: 16,
            paddingVertical: 6,
            backgroundColor: border,
            borderRadius: 8,
          }}
        >
          <ThemedText>{actionLabel}</ThemedText>
        </Pressable>
      )}
    </View>
  );
}
