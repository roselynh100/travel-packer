import { CameraView, useCameraPermissions } from "expo-camera";
import { useIsFocused } from "@react-navigation/native";
import { useState, useRef } from "react";
import {
  Alert,
  Button,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
  Image,
  ActivityIndicator,
  Platform,
} from "react-native";
import { API_BASE_URL } from "@/constants/api";
import { ThemedText } from "@/components/themed-text";

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
      <View style={styles.container}>
        <Text style={styles.message}>
          We need your permission to use the camera.
        </Text>
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
    <View style={styles.container}>
      {isFocused && !capturedPhoto && (
        <CameraView style={styles.camera} facing="back" ref={cameraRef} />
      )}
      {capturedPhoto && (
        <Image source={{ uri: capturedPhoto }} style={styles.camera} />
      )}
      {(isCapturing || isUploading) && (
        <View style={styles.overlay}>
          <ActivityIndicator size="large" color="#fff" />
          <Text style={styles.overlayText}>
            {isUploading ? "Uploading..." : "Capturing..."}
          </Text>
        </View>
      )}
      <View style={styles.buttonContainer}>
        <TouchableOpacity
          style={[
            styles.button,
            (isCapturing || isUploading) && styles.buttonDisabled,
          ]}
          onPress={handleScan}
          disabled={isCapturing || isUploading}
        >
          <ThemedText type="subtitle">Scan Item</ThemedText>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: "center",
  },
  message: {
    textAlign: "center",
    paddingBottom: 10,
  },
  camera: {
    flex: 1,
  },
  buttonContainer: {
    position: "absolute",
    bottom: 64,
    flexDirection: "row",
    backgroundColor: "transparent",
    width: "100%",
    paddingHorizontal: 64,
  },
  button: {
    flex: 1,
    alignItems: "center",
  },
  buttonDisabled: {
    opacity: 0.5,
  },
  overlay: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "rgba(0, 0, 0, 0.5)",
    justifyContent: "center",
    alignItems: "center",
  },
  overlayText: {
    color: "white",
    fontSize: 18,
    marginTop: 16,
    fontWeight: "bold",
  },
});
