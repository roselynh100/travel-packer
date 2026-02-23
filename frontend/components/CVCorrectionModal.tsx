import { Modal, View } from "react-native";

import { CVResult } from "@/constants/types";
import { ThemedButton } from "@/components/ThemedButton";
import { ThemedText } from "@/components/ThemedText";

type CVCorrectionModalProps = {
  visible: boolean;
  cvResults: CVResult[] | null;
  onSelect: (choice: CVResult) => void;
  onDismiss: () => void;
};

export function CVCorrectionModal({
  visible,
  cvResults,
  onSelect,
  onDismiss,
}: CVCorrectionModalProps) {
  if (!cvResults || cvResults.length === 0) {
    return null;
  }

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onDismiss}
    >
      <View className="flex-1 justify-center items-center bg-black/70 px-6">
        <View className="bg-[var(--color-bg-nav)] rounded-2xl p-12 items-center">
          <ThemedText type="subtitle" className="text-center mb-4">
            What did you just scan?
          </ThemedText>
          <View className="w-full gap-3 mt-2">
            {cvResults.map((option) => {
              const percent = Math.round(option.confidence_score * 100);
              return (
                <ThemedButton
                  key={option.item_name}
                  title={`${option.item_name} (${percent}% confidence)`}
                  onPress={() => onSelect(option)}
                  className="w-full"
                />
              );
            })}
          </View>
        </View>
      </View>
    </Modal>
  );
}
