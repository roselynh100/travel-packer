import { useEffect, useState } from "react";
import { ActivityIndicator, Modal, View } from "react-native";

import { API_BASE_URL } from "@/constants/api";
import { Item } from "@/constants/types";
import { ThemedButton } from "@/components/ThemedButton";
import { ThemedText } from "@/components/ThemedText";

type WeightModalStatus = "pending" | "success";

type WeightModalProps = {
  visible: boolean;
  onClose: () => void;
  /**
   * Called when a weight has been successfully read and the user closes the modal.
   * Passes the backend Item so we can use it in the scan (CV detection) flow.
   */
  onWeightReady: (item: Item) => void;
};

export function WeightModal({
  visible,
  onClose,
  onWeightReady,
}: WeightModalProps) {
  const [status, setStatus] = useState<WeightModalStatus>("pending");
  const [countdown, setCountdown] = useState<number>(-1);
  const [weightItem, setWeightItem] = useState<Item | null>(null);

  // Reset and start countdown when modal opens
  useEffect(() => {
    if (visible) {
      setStatus("pending");
      setCountdown(5);
      setWeightItem(null);
    }
  }, [visible]);

  // Countdown from 5 (after that we show a spinner until the weight call completes)
  useEffect(() => {
    if (!visible || countdown < 0) return;

    // When countdown hits 0, stop counting (spinner will take over)
    if (countdown === 0) {
      setCountdown(-1);
      return;
    }

    const timeoutId = setTimeout(() => {
      setCountdown((prev) => prev - 1);
    }, 1000);

    return () => clearTimeout(timeoutId);
  }, [visible, status, countdown]);

  useEffect(() => {
    if (!visible || status !== "pending") return;

    (async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/items/weight`, {
          method: "POST",
        });

        if (!response.ok) {
          // If weight fails (e.g. scale disconnected), just close the modal
          // and let the user proceed without weight.
          onClose();
          return;
        }

        const result: Item = await response.json();
        setWeightItem(result);
        setStatus("success");
      } catch {
        onClose();
      }
    })();
  }, [visible, status, onClose]);

  const handleNext = () => {
    if (!weightItem) return;
    onWeightReady(weightItem);
    onClose();
  };

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={() => status === "success" && handleNext()}
    >
      <View className="flex-1 justify-center items-center bg-black/70 px-6">
        <View className="bg-[var(--color-bg-nav)] rounded-2xl p-12 items-center w-full max-w-sm">
          <ThemedText type="subtitle" className="text-center mb-4">
            Place item in middle of scale
          </ThemedText>
          {countdown >= 0 && (
            <ThemedText type="title" className="text-4xl mb-6">
              {countdown}
            </ThemedText>
          )}
          {countdown < 0 && status === "pending" && (
            <>
              <ActivityIndicator size="large" color="#fff" />
              <ThemedText type="subtitle" className="mt-4">
                Reading weight...
              </ThemedText>
            </>
          )}
          {status === "success" && weightItem && (
            <>
              <ThemedText type="subtitle" className="mb-2">
                Weight:{" "}
                {weightItem.weight_kg != null
                  ? `${weightItem.weight_kg} kg`
                  : "—"}
              </ThemedText>
              <ThemedButton
                title="Next"
                onPress={handleNext}
                className="mt-4"
              />
            </>
          )}
        </View>
      </View>
    </Modal>
  );
}
