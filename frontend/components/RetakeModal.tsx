import { Modal, View } from "react-native";

import { ThemedButton } from "@/components/ThemedButton";
import { ThemedText } from "@/components/ThemedText";
import { useTheme } from "@/theme/useTheme";

type RetakeModalProps = {
  visible: boolean;
  onConfirm: () => void;
};

export function RetakeModal({ visible, onConfirm }: RetakeModalProps) {
  const theme = useTheme();

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onConfirm}
    >
      <View className="flex-1 justify-center items-center bg-black/70 px-6">
        <View
          className="rounded-2xl p-12 items-center max-w-md w-full"
          style={{ backgroundColor: theme.bgNav }}
        >
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
    </Modal>
  );
}
