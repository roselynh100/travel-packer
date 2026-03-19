import { Pressable } from "react-native";

import { IconSymbol } from "@/components/ui/icon-symbol";
import { useTheme } from "@/theme/useTheme";

type ModalCloseButtonProps = {
  onPress: () => void;
};

export function ModalCloseButton({ onPress }: ModalCloseButtonProps) {
  const theme = useTheme();

  return (
    <Pressable
      onPress={(e) => {
        e.stopPropagation();
        onPress();
      }}
      hitSlop={10}
      className="absolute top-3 right-3"
      style={({ pressed }) => ({
        opacity: pressed ? 0.7 : 1,
      })}
    >
      <IconSymbol name="xmark" size={20} color={theme.text} />
    </Pressable>
  );
}

