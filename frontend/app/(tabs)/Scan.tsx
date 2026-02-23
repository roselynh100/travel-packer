import { CameraView, useCameraPermissions } from "expo-camera";
import { useIsFocused } from "@react-navigation/native";
import { useState, useRef, useEffect } from "react";
import { Button, View, ActivityIndicator, Platform } from "react-native";

import { API_BASE_URL } from "@/constants/api";
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
import { BoundingBoxOverlay } from "@/components/BoundingBoxOverlay";
import { cn } from "@/helpers/cn";

const CAMERA_CAPTURE_DELAY = 1500;

// TODO: Merge CVResult and currentItem???
export default function ScanningScreen() {
  const { tripId, currentItem, setCurrentItem } = useAppContext();
  const [permission, requestPermission] = useCameraPermissions();

  const cameraRef = useRef<CameraView>(null);

  const [weightModalVisible, setWeightModalVisible] = useState(false);
  const [weightItem, setWeightItem] = useState<Item | null>(null);
  const [isCapturing, setIsCapturing] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [capturedPhoto, setCapturedPhoto] = useState<string | null>(null);
  const [cvResults, setCvResults] = useState<CVResult[] | null>(null);
  const [infoBanner, setInfoBanner] = useState<{
    type: "error" | "info";
    message: string;
  } | null>(null);
  const [correctionModalVisible, setCorrectionModalVisible] = useState(false);

  const isFocused = useIsFocused();

  useEffect(() => {
    setWeightModalVisible(isFocused);
  }, [isFocused]);

  // Camera permissions are still loading
  if (!permission) {
    return <View />;
  }

  // Camera permissions are not granted yet
  if (!permission.granted) {
    return (
      <View className="flex-1">
        <ThemedText>We need your permission to use the camera.</ThemedText>
        <Button onPress={requestPermission} title="grant permission" />
      </View>
    );
  }

  // TODO: Clean up this function
  async function handleScan() {
    if (!cameraRef.current || isCapturing || isUploading) return;

    try {
      // Clear any previous results when starting a new scan
      setInfoBanner(null);
      setCvResults(null);

      setIsCapturing(true);

      const photo = await cameraRef.current.takePictureAsync();
      setCapturedPhoto(photo.uri);
      console.log("Photo captured successfully:", photo.uri);

      // Let the "capturing" load for a bit, then send to API and reset camera
      await new Promise((resolve) => setTimeout(resolve, CAMERA_CAPTURE_DELAY));

      // When scale is connected, we'll already have an item created (with only weight)
      const { item: uploadedItem, shouldDelayPacking } = await uploadPhotoToAPI(
        photo.uri,
        weightItem?.item_id,
      );

      // Only fetch packing recommendation immediately when we are confident about the CV result.
      // If low confidence, we defer this until after the user confirms the correct item.
      if (uploadedItem?.item_id && !shouldDelayPacking) {
        await getPackingRecommendation(uploadedItem.item_id);
      }
    } catch (error) {
      console.error("Error capturing photo:", error);

      const apiError = error as any;
      if (apiError.status === 500) {
        setInfoBanner({
          type: "error",
          message: "YOLO error - object not in target list",
        });
      } else if (apiError.status === 404) {
        setInfoBanner({
          type: "error",
          message: "App error - trip not found",
        });
      } else {
        setInfoBanner({
          type: "error",
          message:
            error instanceof Error ? error.message : "Failed to scan item",
        });
      }
    } finally {
      setIsCapturing(false);
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
        ? `${API_BASE_URL}/items/detect?item_id=${encodeURIComponent(itemId)}`
        : `${API_BASE_URL}/items/detect`;

      const response = await fetch(detectUrl, {
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

      const { item, cv_candidates } = result;
      setCvResults(cv_candidates);

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
    try {
      const response = await fetch(
        `${API_BASE_URL}/trips/${tripId}/item/${itemId}/packing-decision`,
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
    } catch (error) {
      console.error("Error getting packing recommendation:", error);
      throw error;
    }
  }

  async function handleCorrectionSelect(choice: CVResult) {
    if (!currentItem) {
      setCorrectionModalVisible(false);
      return;
    }

    try {
      const response = await fetch(
        `${API_BASE_URL}/items/${encodeURIComponent(currentItem.item_id)}`,
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

      setCvResults([choice]);
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
      {isFocused && !capturedPhoto && (
        <CameraView
          facing="back"
          ref={cameraRef}
          zoom={0.1}
          style={{ flex: 1 }}
        />
      )}
      {capturedPhoto && (
        <BoundingBoxOverlay
          uri={capturedPhoto}
          cvResult={cvResults?.[0] ?? null}
          isCapturing={isCapturing}
          isUploading={isUploading}
        />
      )}
      <CVCorrectionModal
        visible={correctionModalVisible && !!capturedPhoto && !isUploading}
        cvResults={cvResults}
        onSelect={handleCorrectionSelect}
        onDismiss={() => setCorrectionModalVisible(false)}
      />
      {capturedPhoto && infoBanner && !isUploading && (
        <View
          className={cn(
            "w-full absolute top-0 left-0 right-0 py-3 items-center",
            infoBanner.type === "error" ? "bg-red-600" : "bg-blue-600",
          )}
        >
          <ThemedText type="subtitle" className="text-white text-center">
            {infoBanner.message}
          </ThemedText>
        </View>
      )}
      {(isCapturing || isUploading) && (
        <View className="w-full h-full absolute bg-black/50 justify-center items-center">
          <ActivityIndicator size="large" color="#fff" />
          <ThemedText type="subtitle" className="text-white mt-8">
            {isUploading ? "Uploading..." : "Capturing..."}
          </ThemedText>
        </View>
      )}
      <View className="w-full absolute bottom-8 items-center">
        {!capturedPhoto && (
          <ThemedButton title="Scan Item" onPress={handleScan} />
        )}
        {capturedPhoto && !isUploading && !isCapturing && (
          <ThemedButton
            title="Scan Again"
            onPress={() => {
              setCapturedPhoto(null);
              setInfoBanner(null);
              setCvResults(null);
            }}
          />
        )}
      </View>
    </View>
  );
}
