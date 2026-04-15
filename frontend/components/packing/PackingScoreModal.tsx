import { useEffect, useState } from "react";
import { Modal, Pressable, View, ActivityIndicator } from "react-native";

import { apiFetch } from "@/constants/api";
import { ThemedButton } from "@/components/ThemedButton";
import { ThemedText } from "@/components/ThemedText";
import { ModalCloseButton } from "@/components/ModalCloseButton";
import { useTheme } from "@/theme/useTheme";

type PackingScoreModalProps = {
  visible: boolean;
  tripId: string | null;
  onClose: () => void;
};

export function PackingScoreModal({
  visible,
  tripId,
  onClose,
}: PackingScoreModalProps) {
  const theme = useTheme();

  const [isLoading, setIsLoading] = useState(false);
  const [score, setScore] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!visible) return;
    if (!tripId) return;

    let didCancel = false;
    (async () => {
      setIsLoading(true);
      setError(null);
      setScore(null);

      try {
        const response = await apiFetch(
          `/trips/${encodeURIComponent(tripId)}/packing-score`,
          { method: "GET" },
        );

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(errorText || `Request failed (${response.status})`);
        }

        const value = (await response.json()) as number;
        if (!didCancel) setScore(value);
      } catch (e) {
        const message =
          e instanceof Error ? e.message : "Failed to load packing score";
        if (!didCancel) setError(message);
      } finally {
        if (!didCancel) setIsLoading(false);
      }
    })();

    return () => {
      didCancel = true;
    };
  }, [visible, tripId]);

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <Pressable
        className="flex-1 justify-center items-center bg-black/70 px-6"
        onPress={onClose}
      >
        <Pressable
          onPress={() => {}}
          className="relative rounded-2xl pt-16 pb-12 px-8 w-full max-w-md"
          style={{ backgroundColor: theme.bgNav }}
        >
          <ModalCloseButton onPress={onClose} />

          <ThemedText type="subtitle" className="text-center mb-3">
            Your packing score:
          </ThemedText>

          {isLoading && (
            <View className="items-center">
              <ActivityIndicator size="large" color={theme.primary} />
              <ThemedText className="mt-4 text-center">{`Calculating...`}</ThemedText>
            </View>
          )}

          {!isLoading && !error && score != null && (
            <View className="items-center">
              <ThemedText type="title">{score.toFixed(2)} / 100</ThemedText>
            </View>
          )}

          {!isLoading && error && (
            <View>
              <ThemedText type="subtitle" className="text-center mb-4">
                Could not load score
              </ThemedText>
              <ThemedText className="text-center">{error}</ThemedText>
            </View>
          )}

          {!isLoading && !error && score != null && (
            <View className="mt-6">
              <ThemedButton
                title="Got it!"
                onPress={onClose}
                className="w-full"
              />
            </View>
          )}

          {!isLoading && error && (
            <View className="mt-6">
              <ThemedButton
                title="Close"
                onPress={onClose}
                className="w-full"
              />
            </View>
          )}
        </Pressable>
      </Pressable>
    </Modal>
  );
}
