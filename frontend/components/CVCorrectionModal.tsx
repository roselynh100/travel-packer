import { useEffect, useState } from "react";
import { Modal, View } from "react-native";

import { CVResult } from "@/constants/types";
import { CV_CLASSES } from "@/constants/cv";
import { ThemedButton } from "@/components/ThemedButton";
import { ThemedText } from "@/components/ThemedText";
import { ThemedDropdown } from "@/components/ThemedDropdown";
import { useTheme } from "@/theme/useTheme";

type CVCorrectionModalProps = {
  visible: boolean;
  currentCvResult: CVResult | null;
  onSelect: (selectedItemName: string) => void;
  onDismiss: () => void;
};

export function CVCorrectionModal({
  visible,
  currentCvResult,
  onSelect,
  onDismiss,
}: CVCorrectionModalProps) {
  const theme = useTheme();
  const [selectedValue, setSelectedValue] = useState<string | null>(null);

  useEffect(() => {
    if (visible && currentCvResult) {
      setSelectedValue(currentCvResult.item_name);
    }
  }, [visible, currentCvResult]);

  if (!currentCvResult) {
    return null;
  }

  const dropdownData = CV_CLASSES.map((name) => ({
    label: name,
    value: name,
  }));

  const handleConfirm = () => {
    if (selectedValue) {
      onSelect(selectedValue);
    }
  };

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onDismiss}
    >
      <View className="flex-1 justify-center items-center bg-black/70 px-6">
        <View
          className="rounded-2xl p-6 w-full max-w-sm"
          style={{ backgroundColor: theme.bgNav }}
        >
          <ThemedText type="subtitle" className="text-center mb-4">
            What did you just scan?
          </ThemedText>
          <View className="w-full mb-4">
            <ThemedDropdown
              data={dropdownData}
              value={selectedValue}
              onChange={setSelectedValue}
              placeholder="Select class"
            />
          </View>
          <ThemedButton
            title="Confirm"
            onPress={handleConfirm}
            className="w-full"
          />
        </View>
      </View>
    </Modal>
  );
}
