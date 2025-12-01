import { useEffect, useState } from "react";
import { View, Image, type LayoutChangeEvent } from "react-native";
import type { CVResult } from "@/constants/types";
import { ThemedText } from "@/components/ThemedText";

type BoundingBoxOverlayProps = {
  uri: string;
  cvResult: CVResult | null;
  isCapturing: boolean;
  isUploading: boolean;
};

type Size = {
  width: number;
  height: number;
};

export function BoundingBoxOverlay({
  uri,
  cvResult,
  isCapturing,
  isUploading,
}: BoundingBoxOverlayProps) {
  const [imageSize, setImageSize] = useState<Size | null>(null);
  const [layoutSize, setLayoutSize] = useState<Size | null>(null);

  useEffect(() => {
    setImageSize(null);
    setLayoutSize(null);

    if (!uri) return;

    Image.getSize(
      uri,
      (width, height) => {
        setImageSize({ width, height });
      },
      (error) => {
        console.warn("Failed to get image size for bounding boxes", error);
      }
    );
  }, [uri]);

  const handleLayout = (event: LayoutChangeEvent) => {
    const { width, height } = event.nativeEvent.layout;
    setLayoutSize({ width, height });
  };

  return (
    <View className="flex-1" onLayout={handleLayout}>
      <Image source={{ uri }} className="flex-1" resizeMode="cover" />
      {!isCapturing &&
        !isUploading &&
        cvResult &&
        imageSize &&
        layoutSize &&
        cvResult.bounding_boxes.map((box, index) => {
          const imgW = imageSize.width;
          const imgH = imageSize.height;
          const containerW = layoutSize.width;
          const containerH = layoutSize.height;

          const scale = Math.max(containerW / imgW, containerH / imgH);
          const displayW = imgW * scale;
          const displayH = imgH * scale;
          const offsetX = (displayW - containerW) / 2;
          const offsetY = (displayH - containerH) / 2;

          const left = box.x_min * scale - offsetX;
          const top = box.y_min * scale - offsetY;
          const boxWidth = (box.x_max - box.x_min) * scale;
          const boxHeight = (box.y_max - box.y_min) * scale;

          return (
            <>
              <ThemedText
                className="text-white absolute bg-green-500 p-2"
                style={{
                  left,
                  top: top - 38,
                }}
              >
                {cvResult.class_name} ({cvResult.confidence_score})
              </ThemedText>
              <View
                key={index}
                className="absolute border-2 border-green-500"
                style={{
                  left,
                  top,
                  width: boxWidth,
                  height: boxHeight,
                }}
              />
            </>
          );
        })}
    </View>
  );
}
