import { CameraView, useCameraPermissions } from "expo-camera";
import { useIsFocused } from "@react-navigation/native";
import { useState, useRef } from "react";
import {
  Alert,
  Button,
  TouchableOpacity,
  View,
  Image,
  ActivityIndicator,
  Platform,
  Text,
} from "react-native";
import { API_BASE_URL } from "@/constants/api";
import { ThemedText } from "@/components/ThemedText";

const CAMERA_CAPTURE_DELAY = 1500;

export default function ScanningScreen() {
  const [permission, requestPermission] = useCameraPermissions();

  const cameraRef = useRef<CameraView>(null);

  const [isCapturing, setIsCapturing] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [capturedPhoto, setCapturedPhoto] = useState<string | null>(null);

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
      setIsCapturing(true);

      const photo = await cameraRef.current.takePictureAsync();
      setCapturedPhoto(photo.uri);
      console.log("Photo captured successfully:", photo.uri);

      // Let the "capturing" load for a bit, then send to API and reset camera
      await new Promise((resolve) => setTimeout(resolve, CAMERA_CAPTURE_DELAY));
      setIsCapturing(false);

      await uploadPhotoToAPI(photo.uri);
    } catch (error) {
      console.error("Error capturing photo:", error);
      Alert.alert(
        "Error",
        error instanceof Error ? error.message : "Failed to scan item"
      );
    } finally {
      setIsCapturing(false);
      setCapturedPhoto(null);
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

      const response = await fetch(`${API_BASE_URL}/items/detect`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `API error (${response.status}): ${errorText || response.statusText}`
        );
      }

      const result = await response.json();
      console.log("Upload success:", result);

      await new Promise((resolve) => setTimeout(resolve, CAMERA_CAPTURE_DELAY));
    } catch (error) {
      console.error("Error uploading photo to API:", error);
      throw error; // Re-throw so handleScan can handle it
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <View className="flex-1">
      {isFocused && !capturedPhoto && (
        <CameraView facing="back" ref={cameraRef} style={{ flex: 1 }} />
      )}
      {capturedPhoto && (
        <Image source={{ uri: capturedPhoto }} className="flex-1" />
      )}
      {(isCapturing || isUploading) && (
        <View className="w-full h-full absolute bg-black/50 justify-center items-center">
          <ActivityIndicator size="large" color="#fff" />
          <Text className={CameraText + " mt-8"}>
            {isUploading ? "Uploading..." : "Capturing..."}
          </Text>
        </View>
      )}
      <View className="w-full absolute bottom-8 items-center">
        <TouchableOpacity
          onPress={handleScan}
          className={isCapturing || isUploading ? "opacity-50" : ""}
          disabled={isCapturing || isUploading}
        >
          <Text className={CameraText}>Scan Item</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const CameraText = "text-white text-xl font-bold";
