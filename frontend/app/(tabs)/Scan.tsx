import { CameraView, useCameraPermissions } from "expo-camera";
import { useIsFocused } from "@react-navigation/native";
import { useState, useRef } from "react";
import { Button, View, ActivityIndicator, Platform } from "react-native";

import { API_BASE_URL } from "@/constants/api";
import { CVResult, Item } from "@/constants/types";
import { useAppContext } from "@/helpers/AppContext";
import { ThemedText } from "@/components/ThemedText";
import { ThemedButton } from "@/components/ThemedButton";
import { BoundingBoxOverlay } from "@/components/BoundingBoxOverlay";
import { cn } from "@/helpers/cn";

const CAMERA_CAPTURE_DELAY = 1500;

export default function ScanningScreen() {
  const { tripId } = useAppContext();
  const [permission, requestPermission] = useCameraPermissions();

  const cameraRef = useRef<CameraView>(null);

  const [isCapturing, setIsCapturing] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [capturedPhoto, setCapturedPhoto] = useState<string | null>(null);
  const [cvResult, setCvResult] = useState<CVResult | null>(null);
  const [infoBanner, setInfoBanner] = useState<{
    type: "error" | "info";
    message: string;
  } | null>(null);

  const isFocused = useIsFocused();

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

  async function handleScan() {
    if (!cameraRef.current || isCapturing || isUploading) return;

    try {
      // Clear any previous results when starting a new scan
      setInfoBanner(null);
      setCvResult(null);

      setIsCapturing(true);

      const photo = await cameraRef.current.takePictureAsync();
      setCapturedPhoto(photo.uri);
      console.log("Photo captured successfully:", photo.uri);

      // Let the "capturing" load for a bit, then send to API and reset camera
      await new Promise((resolve) => setTimeout(resolve, CAMERA_CAPTURE_DELAY));

      await uploadPhotoToAPI(photo.uri);
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

  async function uploadPhotoToAPI(uri: string) {
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
          })
        );
      } else {
        // iOS and Android - use the file URI directly
        formData.append("image", {
          uri,
          name: "image.jpg",
          type: "image/jpeg",
        } as any);
      }

      const response = await fetch(
        `${API_BASE_URL}/items/detect?trip_id=${tripId}`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        const errorText = await response.text();
        const error: any = new Error(
          `API error (${response.status}): ${errorText || response.statusText}`
        );
        error.status = response.status;
        throw error;
      }

      const result: Item = await response.json();
      console.log("Upload success:", result);

      setCvResult(result.cv_results[0]);

      await new Promise((resolve) => setTimeout(resolve, CAMERA_CAPTURE_DELAY));
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <View className="flex-1">
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
          cvResult={cvResult}
          isCapturing={isCapturing}
          isUploading={isUploading}
        />
      )}
      {capturedPhoto && infoBanner && !isUploading && (
        <View
          className={cn(
            "w-full absolute top-0 left-0 right-0 py-3 items-center",
            infoBanner.type === "error" ? "bg-red-600" : "bg-blue-600"
          )}
        >
          <ThemedText type="subtitle" className="text-white">
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
              setCvResult(null);
            }}
          />
        )}
      </View>
    </View>
  );
}
