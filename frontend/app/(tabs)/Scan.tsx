import { useCameraPermissions } from "expo-camera";
import { useIsFocused } from "@react-navigation/native";
import { useCallback, useEffect, useState } from "react";
import { Button, View, Image, type LayoutChangeEvent } from "react-native";

import { Item } from "@/constants/types";
import { ThemedText } from "@/components/ThemedText";
import { ThemedButton } from "@/components/ThemedButton";
import { WeightModal } from "@/components/WeightModal";
import { RetakeModal } from "@/components/RetakeModal";
import { CVCorrectionModal } from "@/components/CVCorrectionModal";
import { CameraCaptureView } from "@/components/CameraCaptureView";
import { ThemedBanner } from "@/components/ThemedBanner";
import { ThemedLoading } from "@/components/ThemedLoading";
import { useScanning } from "@/hooks/useScanning";

// TODO: Merge CVResult and currentItem???
export default function ScanningScreen() {
  const [permission, requestPermission] = useCameraPermissions();

  const [weightModalVisible, setWeightModalVisible] = useState(false);
  const [weightItem, setWeightItem] = useState<Item | null>(null);
  const [resultImageSize, setResultImageSize] = useState<number | null>(null);

  const isFocused = useIsFocused();

  const {
    scanResult,
    isProcessing,
    infoBanner,
    retakeModalVisible,
    correctionModalVisible,
    handleCaptured,
    handleRetakeConfirm,
    openCorrectionModal,
    handleCorrectionSelect,
    dismissCorrectionModal,
    clearScanResult,
  } = useScanning(weightItem);

  const onResultImageLayout = useCallback((e: LayoutChangeEvent) => {
    const { width, height } = e.nativeEvent.layout;
    setResultImageSize(Math.min(width, height));
  }, []);

  useEffect(() => {
    setWeightModalVisible(isFocused);
    if (!isFocused) {
      setResultImageSize(null);
      clearScanResult();
    }
  }, [isFocused, clearScanResult]);

  if (!permission) {
    return <View />;
  }

  if (!permission.granted) {
    return (
      <View className="flex-1">
        <ThemedText>We need your permission to use the camera.</ThemedText>
        <Button onPress={requestPermission} title="grant permission" />
      </View>
    );
  }

  return (
    <View className="flex-1">
      <WeightModal
        visible={weightModalVisible}
        onClose={() => setWeightModalVisible(false)}
        onWeightReady={setWeightItem}
      />
      {isFocused && !scanResult && !isProcessing && (
        <CameraCaptureView onCaptured={handleCaptured} />
      )}
      {scanResult && (
        <>
          {infoBanner && (
            <ThemedBanner
              type={infoBanner.type}
              message={infoBanner.message}
              actionLabel={infoBanner.actionLabel}
              onActionPress={infoBanner.onActionPress}
            />
          )}
          <View
            className="flex-1 items-center justify-center"
            onLayout={onResultImageLayout}
          >
            {resultImageSize != null && (
              <View
                style={{ width: resultImageSize, height: resultImageSize }}
                className="bg-black"
              >
                <Image
                  source={{
                    uri: scanResult.annotatedUri ?? scanResult.photoUri,
                  }}
                  className="w-full h-full"
                  resizeMode="contain"
                />
              </View>
            )}
          </View>
        </>
      )}
      <RetakeModal
        visible={retakeModalVisible}
        onConfirm={handleRetakeConfirm}
      />
      <CVCorrectionModal
        visible={correctionModalVisible}
        currentCvResult={scanResult?.cvResult ?? null}
        onSelect={handleCorrectionSelect}
        onDismiss={dismissCorrectionModal}
      />
      <ThemedLoading isLoading={isProcessing} message="Processing..." />
      {scanResult && !isProcessing && (
        <View className="w-full absolute bottom-8 items-center">
          <ThemedButton title="Wrong item?" onPress={openCorrectionModal} />
        </View>
      )}
    </View>
  );
}
