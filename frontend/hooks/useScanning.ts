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
import { CAMERA_CAPTURE_DELAY, CONFIDENCE_THRESHOLD } from "@/constants/cv";

type ScanResult = {
  photoUri: string;
  annotatedUri: string | null;
  cvResult: CVResult | null;
} | null;

type DetectRun = {
  cvResult: CVResult;
  annotatedUri: string | null;
  itemId: string;
};

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

export function useScanning(weightItem: Item | null) {
  const { tripId, currentItem, setCurrentItem } = useAppContext();
  const router = useRouter();

  const [isProcessing, setIsProcessing] = useState(false);
  const [scanResult, setScanResult] = useState<ScanResult>(null);
  const [infoBanner, setInfoBanner] = useState<ThemedBannerProps | null>(null);
  const [originalDetect, setOriginalDetect] = useState<DetectRun | null>(null);
  const [retakeModalVisible, setRetakeModalVisible] = useState(false);
  const [correctionModalVisible, setCorrectionModalVisible] = useState(false);

  const clearScanResult = useCallback(() => {
    setIsProcessing(false);
    setScanResult(null);
    setInfoBanner(null);
    setOriginalDetect(null);
    setRetakeModalVisible(false);
    setCorrectionModalVisible(false);
  }, []);

  // Reset when a new trip starts
  useEffect(() => {
    if (tripId) clearScanResult();
  }, [tripId, clearScanResult]);

  const uploadPhotoToAPI = useCallback(
    async (
      uri: string,
      itemId?: string,
    ): Promise<{
      item: Item;
      cvResult: CVResult;
      annotatedUri: string | null;
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
      const { item, annotated_image } = result;
      const cvResult = item.cv_result!;
      const annotatedUri = annotated_image
        ? `data:image/jpeg;base64,${annotated_image}`
        : null;

      return { item, cvResult, annotatedUri };
    },
    [],
  );

  const getPackingRecommendation = useCallback(
    async (itemId: string) => {
      if (!tripId) return;

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
          packing_recommendation: result,
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
        cvResult: null,
      });
      setIsProcessing(true);

      try {
        await delay(CAMERA_CAPTURE_DELAY);

        const { item, cvResult, annotatedUri } = await uploadPhotoToAPI(
          squareUri,
          weightItem?.item_id,
        );

        if (originalDetect) {
          const secondRun: DetectRun = {
            cvResult,
            annotatedUri,
            itemId: item.item_id,
          };
          const best =
            originalDetect.cvResult.confidence_score >=
            cvResult.confidence_score
              ? originalDetect
              : secondRun;

          // Use the higher confidence score
          setScanResult({
            photoUri: squareUri,
            annotatedUri: best.annotatedUri,
            cvResult: best.cvResult,
          });
          setOriginalDetect(null);

          if (best === originalDetect) {
            // We've just overwritten the original detection, so update it back
            await apiFetch(`/items/${encodeURIComponent(item.item_id)}`, {
              method: "PATCH",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ cv_result: originalDetect.cvResult }),
            });

            setCurrentItem((prev) =>
              prev?.item_id === item.item_id
                ? {
                    ...(prev as ItemWithPackingRecommendation),
                    item_name: originalDetect.cvResult.item_name,
                    cv_result: originalDetect.cvResult,
                    packing_recommendation: null,
                  }
                : prev,
            );
          } else {
            const bestItem: ItemWithPackingRecommendation = {
              ...item,
              item_name: best.cvResult.item_name,
              cv_result: best.cvResult,
              packing_recommendation: null,
            };
            setCurrentItem(bestItem);
          }
          await getPackingRecommendation(item.item_id);
        } else {
          // This is the first capture
          if (cvResult.confidence_score < CONFIDENCE_THRESHOLD) {
            // Low confidence: remember this run but do NOT update currentItem/packing list yet
            setOriginalDetect({
              cvResult,
              annotatedUri,
              itemId: item.item_id,
            });
            setRetakeModalVisible(true);

            // Clear result and show camera again
            setScanResult(null);
          } else {
            setScanResult({ photoUri: squareUri, annotatedUri, cvResult });

            const updatedItem: ItemWithPackingRecommendation = {
              ...item,
              item_name: item.cv_result!.item_name,
              packing_recommendation: null,
            };
            setCurrentItem(updatedItem);

            await getPackingRecommendation(item.item_id);
          }
        }
        await delay(CAMERA_CAPTURE_DELAY);
      } catch (error) {
        const apiErr = error as { status?: number };
        // If retake failed (e.g. no detections) but we have a low-confidence original,
        // fall back to the original detection and treat it as final.
        if (originalDetect && apiErr.status === 500) {
          try {
            // Show the original annotated image / result
            setScanResult({
              photoUri: squareUri,
              annotatedUri: originalDetect.annotatedUri,
              cvResult: originalDetect.cvResult,
            });
            setOriginalDetect(null);

            // Patch backend item to use the original cv_result, then get packing rec
            const response = await apiFetch(
              `/items/${encodeURIComponent(originalDetect.itemId)}`,
              {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ cv_result: originalDetect.cvResult }),
              },
            );
            if (!response.ok) {
              const errorText = await response.text();
              throw new Error(
                `API error (${response.status}): ${errorText || response.statusText}`,
              );
            }

            const updatedItem: Item = await response.json();
            const updatedCv = updatedItem.cv_result!;
            setCurrentItem({
              ...(updatedItem as ItemWithPackingRecommendation),
              item_name: updatedCv.item_name,
              cv_result: updatedCv,
              packing_recommendation: null,
            });

            await getPackingRecommendation(updatedItem.item_id);
          } catch (fallbackError) {
            setBannerFromApiError(fallbackError, setInfoBanner);
          }
        } else {
          // First detect failed: keep last photo and show error
          setBannerFromApiError(error, setInfoBanner);
        }
      } finally {
        setIsProcessing(false);
      }
    },
    [
      getPackingRecommendation,
      uploadPhotoToAPI,
      weightItem?.item_id,
      originalDetect,
      setCurrentItem,
    ],
  );

  const handleRetakeConfirm = useCallback(() => {
    setRetakeModalVisible(false);
    setScanResult(null);
  }, []);

  const openCorrectionModal = useCallback(
    () => setCorrectionModalVisible(true),
    [],
  );
  const dismissCorrectionModal = useCallback(
    () => setCorrectionModalVisible(false),
    [],
  );

  const handleCorrectionSelect = useCallback(
    async (selectedItemName: string) => {
      if (!currentItem || !scanResult?.cvResult) {
        setCorrectionModalVisible(false);
        return;
      }

      const newCvResult: CVResult = {
        ...scanResult.cvResult,
        item_name: selectedItemName,
      };

      try {
        const response = await apiFetch(
          `/items/${encodeURIComponent(currentItem.item_id)}`,
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ cv_result: newCvResult }),
          },
        );
        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(
            `API error (${response.status}): ${errorText || response.statusText}`,
          );
        }

        const updatedServerItem: Item = await response.json();
        const updatedCv = updatedServerItem.cv_result!;
        setScanResult((prev) =>
          prev ? { ...prev, cvResult: updatedCv } : null,
        );
        setCurrentItem({
          ...(currentItem as ItemWithPackingRecommendation),
          item_name: selectedItemName,
          cv_result: updatedCv,
          packing_recommendation: null,
        });
        await getPackingRecommendation(currentItem.item_id);
        router.push("/Trips");
      } catch {
        setInfoBanner({
          type: "error",
          message: "Failed to update item classification. Please try again.",
        });
      } finally {
        setCorrectionModalVisible(false);
      }
    },
    [
      currentItem,
      scanResult?.cvResult,
      getPackingRecommendation,
      setCurrentItem,
      router,
    ],
  );

  return {
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
  };
}
