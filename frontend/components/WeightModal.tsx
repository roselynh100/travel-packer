import { useEffect, useState } from "react";
import { ActivityIndicator, Modal, View } from "react-native";

import { apiFetch } from "@/constants/api";
import { Item } from "@/constants/types";
import { ThemedButton } from "@/components/ThemedButton";
import { ThemedText } from "@/components/ThemedText";
import { useTheme } from "@/theme/useTheme";

type WeightModalStatus = "intro" | "pending" | "success";

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
  const [status, setStatus] = useState<WeightModalStatus>("intro");
  const [countdown, setCountdown] = useState<number>(-1);
  const [weightItem, setWeightItem] = useState<Item | null>(null);

  // Reset when modal opens
  useEffect(() => {
    if (visible) {
      setStatus("intro");
      setCountdown(-1);
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
        const response = await apiFetch("/items/weight", {
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

  const handleConfirmEmptyScale = () => {
    // User has confirmed the scale is empty; start countdown and begin reading
    setStatus("pending");
    setCountdown(5);
  };

  const handleNext = () => {
    if (!weightItem) return;
    onWeightReady(weightItem);
    onClose();
  };

  const theme = useTheme();

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={() => status === "success" && handleNext()}
    >
      <View className="flex-1 justify-center items-center bg-black/70 px-6">
        <View
          className="rounded-2xl p-12 items-center"
          style={{ backgroundColor: theme.bgNav }}
        >
          {status === "intro" && (
            <>
              <ThemedText type="subtitle" className="text-center mb-4">
                Get ready to weigh your item
              </ThemedText>
              <ThemedText className="text-center mb-6">
                Please make sure nothing is on the scale.
              </ThemedText>
              <ThemedButton
                title="I'm ready"
                onPress={handleConfirmEmptyScale}
              />
            </>
          )}
          {status !== "intro" && (
            <>
              <ThemedText type="subtitle" className="text-center mb-4">
                For accurate results, place the item in the middle of the scale.
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
            </>
          )}
        </View>
      </View>
    </Modal>
  );
}
