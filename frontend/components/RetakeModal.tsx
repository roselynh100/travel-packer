import { View } from "react-native";

import { ThemedButton } from "@/components/ThemedButton";
import { ThemedText } from "@/components/ThemedText";
import { ModalCloseButton } from "@/components/ModalCloseButton";
import { useTheme } from "@/theme/useTheme";

type RetakeModalProps = {
  visible: boolean;
  onConfirm: () => void;
};

export function RetakeModal({ visible, onConfirm }: RetakeModalProps) {
  const theme = useTheme();

  if (!visible) return null;

  return (
    <View
      style={{
        position: "absolute",
        top: 0,
        right: 0,
        bottom: 0,
        left: 0,
        backgroundColor: "rgba(0,0,0,0.7)",
        zIndex: 999,
      }}
    >
      <View className="flex-1 justify-center items-center px-6">
        <View
          className="relative rounded-2xl p-12 items-center max-w-md w-full"
          style={{ backgroundColor: theme.bgNav }}
        >
          <ModalCloseButton onPress={onConfirm} />
          <ThemedText type="subtitle" className="text-center mb-8">
            Let us make sure we correctly identified your item.
          </ThemedText>
          <ThemedText className="text-center mb-8">
            Please take another photo with a clear background. If it&apos;s a
            piece of clothing, please ensure it&apos;s unfolded.
          </ThemedText>
          <ThemedButton
            title="Scan again"
            onPress={onConfirm}
            className="w-full"
          />
        </View>
      </View>
    </View>
  );
}
