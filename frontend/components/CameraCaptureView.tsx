import { useRef } from "react";
import { Image, View, useWindowDimensions } from "react-native";
import { CameraView } from "expo-camera";
import { ImageManipulator, SaveFormat } from "expo-image-manipulator";
import { ThemedButton } from "@/components/ThemedButton";

type Props = {
  onCaptureStart: () => void;
  onCaptured: (squareUri: string) => void;
  onCaptureEnd: () => void;
};

/**
 * The user's camera view is square, but takePictureAsync() takes a photo using the full available frame.
 * This crops the image to the middle portion that matches what the user saw in the viewfinder.
 */
async function cropToCenterSquare(uri: string): Promise<string> {
  const { width, height } = await new Promise<{
    width: number;
    height: number;
  }>((resolve, reject) =>
    Image.getSize(uri, (w, h) => resolve({ width: w, height: h }), reject),
  );
  const size = Math.min(width, height);
  const context = ImageManipulator.manipulate(uri);
  try {
    const rendered = await context
      .crop({
        originX: (width - size) / 2,
        originY: (height - size) / 2,
        width: size,
        height: size,
      })
      .renderAsync();
    try {
      const result = await rendered.saveAsync({ format: SaveFormat.JPEG });
      return result.uri;
    } finally {
      rendered.release();
    }
  } finally {
    context.release();
  }
}

export function CameraCaptureView({
  onCaptureStart,
  onCaptured,
  onCaptureEnd,
}: Props) {
  const cameraRef = useRef<CameraView>(null);
  const { width: screenWidth, height: screenHeight } = useWindowDimensions();
  const size = Math.min(screenWidth, screenHeight);

  async function handleCapturePress() {
    if (!cameraRef.current) return;

    onCaptureStart();
    try {
      const photo = await cameraRef.current.takePictureAsync();
      if (!photo?.uri) throw new Error("Failed to take picture");
      const squareUri = await cropToCenterSquare(photo.uri);
      onCaptured(squareUri);
    } finally {
      onCaptureEnd();
    }
  }

  return (
    <View className="flex-1">
      <View className="flex-1 items-center justify-center">
        <View style={{ width: size, height: size }} className="overflow-hidden">
          <CameraView
            facing="back"
            ref={cameraRef}
            zoom={0.1}
            style={{ width: size, height: size }}
          />
        </View>
      </View>
      <View className="w-full absolute bottom-8 items-center">
        <ThemedButton title="Scan Item" onPress={handleCapturePress} />
      </View>
    </View>
  );
}
