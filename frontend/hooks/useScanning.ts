import { useCallback, useEffect, useState } from "react";
import { Platform } from "react-native";
import { useRouter } from "expo-router";

import { apiFetch } from "@/constants/api";
import {
  CVResult,
  DetectResponse,
  Item,
  ItemWithPackingRecommendation,
  PackingRecommendation,
} from "@/constants/types";
import { useAppContext } from "@/helpers/AppContext";
import { ThemedBannerProps } from "@/components/ThemedBanner";
import { delay } from "@/helpers/delay";

const CAMERA_CAPTURE_DELAY = 1500;

type ScanResult = {
  photoUri: string;
  annotatedUri: string | null;
  cvResults: CVResult[];
} | null;

function setBannerFromApiError(
  error: unknown,
  setInfoBanner: (b: ThemedBannerProps | null) => void,
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

type UseScanningResult = {
  scanResult: ScanResult;
  isProcessing: boolean;
  infoBanner: ThemedBannerProps | null;
  correctionModalVisible: boolean;
  handleCaptured: (squareUri: string) => Promise<void>;
  handleCorrectionSelect: (choice: CVResult) => Promise<void>;
  dismissCorrectionModal: () => void;
  clearScanResult: () => void;
};

export function useScanning(weightItem: Item | null): UseScanningResult {
  const { tripId, currentItem, setCurrentItem } = useAppContext();
  const router = useRouter();

  const [isProcessing, setIsProcessing] = useState(false);
  const [scanResult, setScanResult] = useState<ScanResult>(null);
  const [infoBanner, setInfoBanner] = useState<ThemedBannerProps | null>(null);
  const [correctionModalVisible, setCorrectionModalVisible] = useState(false);

  const clearScanResult = useCallback(() => {
    setIsProcessing(false);
    setScanResult(null);
    setInfoBanner(null);
    setCorrectionModalVisible(false);
  }, []);

  // Reset when a new trip starts
  useEffect(() => {
    if (!tripId) return;
    clearScanResult();
  }, [tripId, clearScanResult]);

  const uploadPhotoToAPI = useCallback(
    async (
      uri: string,
      itemId?: string,
    ): Promise<{
      item: ItemWithPackingRecommendation | null;
      shouldDelayPacking: boolean;
    }> => {
      const formData = new FormData();

      if (Platform.OS === "web") {
        const response = await fetch(uri);
        const blob = await response.blob();
        formData.append(
          "image",
          new File([blob], "image.jpg", {
            type: "image/jpeg",
          }),
        );
      } else {
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
      setScanResult({
        photoUri: uri,
        cvResults: cv_candidates,
        annotatedUri: annotated_image
          ? `data:image/jpeg;base64,${annotated_image}`
          : null,
      });

      const updatedItem: ItemWithPackingRecommendation = {
        ...item,
        item_name: item.cv_result.item_name,
        packing_recommendation: null,
        packing_recommendation_details: null,
      };
      setCurrentItem(updatedItem);

      const shouldDelayPacking = cv_candidates.length > 1;

      if (shouldDelayPacking) {
        setCorrectionModalVisible(true);
        setInfoBanner({
          type: "warning",
          message: "We’re not fully sure what this is—please confirm below.",
        });
      }

      await delay(CAMERA_CAPTURE_DELAY);

      return { item: updatedItem, shouldDelayPacking };
    },
    [setCurrentItem],
  );

  const getPackingRecommendation = useCallback(
    async (itemId: string) => {
      if (!tripId) {
        return;
      }

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

      setCurrentItem((prevItem) => {
        if (!prevItem || prevItem.item_id !== itemId) {
          return prevItem;
        }
        const typedPrev = prevItem as ItemWithPackingRecommendation;
        return {
          ...typedPrev,
          packing_recommendation: result.status,
          packing_recommendation_details: result,
        };
      });

      if (result.status === "pack") {
        setInfoBanner({
          type: "success",
          message: "This item should be packed!",
          actionLabel: "View",
          onActionPress: () => {
            router.push("/Trips");
          },
        });
      } else if (result.status === "remove") {
        setInfoBanner({
          type: "error",
          message: "This item should be left behind!",
          actionLabel: "View",
          onActionPress: () => {
            router.push({
              pathname: "/Trips",
              params: { packingDecision: "remove" },
            });
          },
        });
      } else if (result.status === "swap") {
        setInfoBanner({
          type: "warning",
          message: "This item should be swapped!",
          actionLabel: "Details",
          onActionPress: () => {
            router.push({
              pathname: "/Trips",
              params: { packingDecision: "swap" },
            });
          },
        });
      }
    },
    [router, tripId, setCurrentItem],
  );

  const handleCaptured = useCallback(
    async (squareUri: string) => {
      setInfoBanner(null);
      setScanResult({
        photoUri: squareUri,
        annotatedUri: null,
        cvResults: [],
      });
      setIsProcessing(true);

      try {
        await delay(CAMERA_CAPTURE_DELAY);

        const { item: uploadedItem, shouldDelayPacking } =
          await uploadPhotoToAPI(squareUri, weightItem?.item_id);

        if (uploadedItem?.item_id && !shouldDelayPacking) {
          await getPackingRecommendation(uploadedItem.item_id);
        }
      } catch (error) {
        console.error("Error after capture:", error);
        setBannerFromApiError(error, setInfoBanner);
      } finally {
        setIsProcessing(false);
      }
    },
    [getPackingRecommendation, uploadPhotoToAPI, weightItem],
  );

  const handleCorrectionSelect = useCallback(
    async (choice: CVResult) => {
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
            `API error (${response.status}): ${
              errorText || response.statusText
            }`,
          );
        }

        const updatedServerItem: Item = await response.json();

        const updatedItem: ItemWithPackingRecommendation = {
          ...(currentItem as ItemWithPackingRecommendation),
          item_name: choice.item_name,
          cv_result: choice,
          // Reset details; they will be re-populated by getPackingRecommendation call
          packing_recommendation: null,
          packing_recommendation_details: null,
        };

        setScanResult((prev) =>
          prev ? { ...prev, cvResults: [choice] } : null,
        );
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
    },
    [currentItem, getPackingRecommendation, setCurrentItem],
  );

  const dismissCorrectionModal = useCallback(() => {
    setCorrectionModalVisible(false);
  }, []);

  return {
    scanResult,
    isProcessing,
    infoBanner,
    correctionModalVisible,
    handleCaptured,
    handleCorrectionSelect,
    dismissCorrectionModal,
    clearScanResult,
  };
}
