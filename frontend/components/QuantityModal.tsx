import { useEffect, useState } from "react";
import { Modal, Pressable, View } from "react-native";

import { ThemedButton } from "@/components/ThemedButton";
import { ThemedText } from "@/components/ThemedText";
import { useTheme } from "@/theme/useTheme";

type QuantityModalProps = {
  visible: boolean;
  itemName: string;
  initialQuantity: number;
  onConfirm: (quantity: number) => void;
  onCancel: () => void;
};

export function QuantityModal({
  visible,
  itemName,
  initialQuantity,
  onConfirm,
  onCancel,
}: QuantityModalProps) {
  const theme = useTheme();
  const [quantity, setQuantity] = useState(initialQuantity);

  useEffect(() => {
    if (visible) {
      setQuantity(initialQuantity);
    }
  }, [visible, initialQuantity]);

  const canDecrement = quantity > 1;
  const canIncrement = quantity < 99;

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onCancel}
    >
      <View className="flex-1 justify-center items-center bg-black/70 px-6">
        <View
          className="rounded-2xl p-10 items-center w-full max-w-md"
          style={{ backgroundColor: theme.bg }}
        >
          <ThemedText type="subtitle" className="text-center mb-6">
            Update quantity of {itemName}
          </ThemedText>
          <View className="flex-row items-center gap-6 mb-8">
            <Pressable
              onPress={() => canDecrement && setQuantity((q) => q - 1)}
              disabled={!canDecrement}
              style={({ pressed }) => ({
                opacity: !canDecrement ? 0.4 : pressed ? 0.7 : 1,
              })}
            >
              <View
                className="rounded-full px-5 py-3"
                style={{
                  backgroundColor: theme.bgNav,
                  borderColor: theme.textPlaceholder,
                  borderWidth: 2,
                }}
              >
                <ThemedText type="subtitle">−</ThemedText>
              </View>
            </Pressable>
            <ThemedText type="title" className="text-4xl">
              {quantity}
            </ThemedText>
            <Pressable
              onPress={() => canIncrement && setQuantity((q) => q + 1)}
              disabled={!canIncrement}
              style={({ pressed }) => ({
                opacity: !canIncrement ? 0.4 : pressed ? 0.7 : 1,
              })}
            >
              <View
                className="rounded-full px-5 py-3"
                style={{
                  backgroundColor: theme.bgNav,
                  borderColor: theme.textPlaceholder,
                  borderWidth: 2,
                }}
              >
                <ThemedText type="subtitle">+</ThemedText>
              </View>
            </Pressable>
          </View>
          <View className="w-full gap-3 mt-4">
            <ThemedButton
              title="Cancel"
              variant="outline"
              onPress={onCancel}
              className="w-full"
            />
            <ThemedButton
              title="Confirm"
              onPress={() => onConfirm(quantity)}
              className="w-full"
            />
          </View>
        </View>
      </View>
    </Modal>
  );
}
