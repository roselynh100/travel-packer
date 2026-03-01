import { useCameraPermissions } from "expo-camera";
import { useIsFocused } from "@react-navigation/native";
import { useState, useEffect, useCallback } from "react";
import {
  Button,
  View,
  Image,
  ActivityIndicator,
  Platform,
  type LayoutChangeEvent,
} from "react-native";

import { apiFetch } from "@/constants/api";
import {
  CVResult,
  DetectResponse,
  Item,
  ItemWithPackingRecommendation,
  PackingRecommendation,
} from "@/constants/types";
import { useAppContext } from "@/helpers/AppContext";
import { ThemedText } from "@/components/ThemedText";
import { ThemedButton } from "@/components/ThemedButton";
import { WeightModal } from "@/components/WeightModal";
import { CVCorrectionModal } from "@/components/CVCorrectionModal";
import { CameraCaptureView } from "@/components/CameraCaptureView";
import { cn } from "@/helpers/cn";

const CAMERA_CAPTURE_DELAY = 1500;

type InfoBanner = { type: "error" | "info"; message: string } | null;

type ScanResult = {
  photoUri: string;
  annotatedUri: string | null;
  cvResults: CVResult[];
} | null;

function setBannerFromApiError(
  error: unknown,
  setInfoBanner: (b: InfoBanner) => void,
) {
  const apiError = error as { status?: number };
  if (apiError.status === 500) {
    setInfoBanner({
      type: "error",
      message: "YOLO error - object not in target list",
    });
  } else if (apiError.status === 404) {
    setInfoBanner({ type: "error", message: "App error - trip not found" });
  } else {
    setInfoBanner({
      type: "error",
      message: error instanceof Error ? error.message : "Failed to scan item",
    });
  }
}

// TODO: Merge CVResult and currentItem???
export default function ScanningScreen() {
  const { tripId, currentItem, setCurrentItem } = useAppContext();
  const [permission, requestPermission] = useCameraPermissions();

  const [weightModalVisible, setWeightModalVisible] = useState(false);
  const [weightItem, setWeightItem] = useState<Item | null>(null);
  const [isCapturing, setIsCapturing] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [scanResult, setScanResult] = useState<ScanResult>(null);
  const [infoBanner, setInfoBanner] = useState<InfoBanner>(null);
  const [correctionModalVisible, setCorrectionModalVisible] = useState(false);
  const [resultImageSize, setResultImageSize] = useState<number | null>(null);

  const isFocused = useIsFocused();

  const onResultImageLayout = useCallback((e: LayoutChangeEvent) => {
    const { width, height } = e.nativeEvent.layout;
    setResultImageSize(Math.min(width, height));
  }, []);

  const clearScanResult = useCallback(() => {
    setScanResult(null);
    setInfoBanner(null);
    setResultImageSize(null);
    setCorrectionModalVisible(false);
  }, []);

  // Reset everything when a new trip starts
  useEffect(() => {
    clearScanResult();
  }, [tripId, clearScanResult]);

  useEffect(() => {
    setWeightModalVisible(isFocused);
  }, [isFocused]);

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

  async function handleCaptured(squareUri: string) {
    setInfoBanner(null);
    setScanResult({
      photoUri: squareUri,
      annotatedUri: null,
      cvResults: [],
    });

    await new Promise((resolve) => setTimeout(resolve, CAMERA_CAPTURE_DELAY));

    try {
      const { item: uploadedItem, shouldDelayPacking } = await uploadPhotoToAPI(
        squareUri,
        weightItem?.item_id,
      );

      if (uploadedItem?.item_id && !shouldDelayPacking) {
        await getPackingRecommendation(uploadedItem.item_id);
      }
    } catch (error) {
      console.error("Error after capture:", error);
      setBannerFromApiError(error, setInfoBanner);
    }
  }

  async function uploadPhotoToAPI(
    uri: string,
    itemId?: string,
  ): Promise<{
    item: ItemWithPackingRecommendation | null;
    shouldDelayPacking: boolean;
  }> {
    try {
      setIsUploading(true);

      const formData = new FormData();

      if (Platform.OS === "web") {
        // On web, uri is a blob URL -> need to fetch and convert it
        const response = await fetch(uri);
        const blob = await response.blob();
        formData.append(
          "image",
          new File([blob], "image.jpg", {
            type: "image/jpeg",
          }),
        );
      } else {
        // iOS and Android - use the file URI directly
        formData.append("image", {
          uri,
          name: "image.jpg",
          type: "image/jpeg",
        } as any);
      }

      const detectUrl = itemId
        ? `/items/detect?item_id=${encodeURIComponent(itemId)}`
        : "/items/detect";

      const response = await apiFetch(detectUrl, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        const error: any = new Error(
          `API error (${response.status}): ${errorText || response.statusText}`,
        );
        error.status = response.status;
        throw error;
      }

      const result: DetectResponse = await response.json();
      console.log("Upload success:", result);

      const { item, cv_candidates, annotated_image } = result;
      setScanResult((prev) =>
        prev
          ? {
              ...prev,
              cvResults: cv_candidates,
              annotatedUri: annotated_image
                ? `data:image/jpeg;base64,${annotated_image}`
                : prev.annotatedUri,
            }
          : null,
      );

      const updatedItem: ItemWithPackingRecommendation = {
        ...item,
        item_name: item.cv_result.item_name,
        packing_recommendation: null,
      };
      setCurrentItem(updatedItem);

      const shouldDelayPacking = cv_candidates.length > 1;

      if (shouldDelayPacking) {
        setCorrectionModalVisible(true);
        setInfoBanner({
          type: "info",
          message: "We’re not fully sure what this is—please confirm below.",
        });
      }

      await new Promise((resolve) => setTimeout(resolve, CAMERA_CAPTURE_DELAY));

      return { item: updatedItem, shouldDelayPacking };
    } finally {
      setIsUploading(false);
    }
  }

  async function getPackingRecommendation(itemId: string) {
    const response = await apiFetch(
      `/trips/${tripId}/item/${itemId}/packing-decision`,
    );

    if (!response.ok) {
      const errorText = await response.text();
      const error: any = new Error(
        `API error (${response.status}): ${errorText || response.statusText}`,
      );
      error.status = response.status;
      throw error;
    }

    const result: PackingRecommendation = await response.json();
    console.log("Packing recommendation received:", result);

    // Only update if currentItem still matches (user hasn't scanned a new item)
    setCurrentItem((prevItem) => {
      if (prevItem?.item_id === itemId) {
        return {
          ...prevItem,
          packing_recommendation: result.status,
        };
      }
      // If item changed, don't update (user scanned a new item)
      return prevItem;
    });

    if (result.status === "pack") {
      setInfoBanner({
        type: "info",
        message: "This item should be packed!",
      });
    } else if (result.status === "remove") {
      setInfoBanner({
        type: "info",
        message: `Do not pack this item. ${result.reason}`,
      });
    } else if (result.status === "swap") {
      setInfoBanner({
        type: "info",
        message: "You must remove an item to pack this one!",
      });
    }
  }

  async function handleCorrectionSelect(choice: CVResult) {
    if (!currentItem) {
      setCorrectionModalVisible(false);
      return;
    }

    try {
      const response = await apiFetch(
        `/items/${encodeURIComponent(currentItem.item_id)}`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ cv_result: choice }),
        },
      );

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `API error (${response.status}): ${errorText || response.statusText}`,
        );
      }

      const updatedServerItem: Item = await response.json();

      const updatedItem: ItemWithPackingRecommendation = {
        ...currentItem,
        item_name: choice.item_name,
        cv_result: choice,
      };

      setScanResult((prev) => (prev ? { ...prev, cvResults: [choice] } : null));
      setCurrentItem(updatedItem);

      if (updatedServerItem.item_id) {
        await getPackingRecommendation(updatedServerItem.item_id);
      }
    } catch (error) {
      console.error("Error correcting item classification:", error);
      setInfoBanner({
        type: "error",
        message: "Failed to update item classification. Please try again.",
      });
    } finally {
      setCorrectionModalVisible(false);
    }
  }

  return (
    <View className="flex-1">
      <WeightModal
        visible={weightModalVisible}
        onClose={() => setWeightModalVisible(false)}
        onWeightReady={setWeightItem}
      />
      {isFocused && !scanResult && (
        <CameraCaptureView
          onCaptureStart={() => setIsCapturing(true)}
          onCaptured={handleCaptured}
          onCaptureEnd={() => setIsCapturing(false)}
        />
      )}
      {scanResult && (
        <>
          {infoBanner && !isUploading && (
            <View
              className={cn(
                "w-full py-3 px-4 items-center",
                infoBanner.type === "error" ? "bg-red-600" : "bg-blue-600",
              )}
            >
              <ThemedText type="subtitle" className="text-white text-center">
                {infoBanner.message}
              </ThemedText>
            </View>
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
      <CVCorrectionModal
        visible={correctionModalVisible && !!scanResult && !isUploading}
        cvResults={scanResult?.cvResults ?? null}
        onSelect={handleCorrectionSelect}
        onDismiss={() => setCorrectionModalVisible(false)}
      />
      {(isCapturing || isUploading) && (
        <View className="w-full h-full absolute bg-black/50 justify-center items-center">
          <ActivityIndicator size="large" color="#fff" />
          <ThemedText type="subtitle" className="text-white mt-8">
            {isUploading ? "Uploading..." : "Capturing..."}
          </ThemedText>
        </View>
      )}
      {scanResult && !isUploading && !isCapturing && (
        <View className="w-full absolute bottom-8 items-center">
          <ThemedButton title="Scan Again" onPress={clearScanResult} />
        </View>
      )}
    </View>
  );
}
