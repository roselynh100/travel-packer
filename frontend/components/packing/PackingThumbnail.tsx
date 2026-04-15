import { useState } from "react";
import { Image, Modal, Pressable, View } from "react-native";

import { useTheme } from "@/theme/useTheme";

type PackingThumbnailProps = {
  photoUri?: string;
};

export function PackingThumbnail({ photoUri }: PackingThumbnailProps) {
  const theme = useTheme();
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);

  if (!photoUri) return null;

  return (
    <>
      <Pressable
        onPress={(e) => {
          e.stopPropagation();
          setIsPreviewOpen(true);
        }}
        style={({ pressed }) => ({
          opacity: pressed ? 0.85 : 1,
        })}
      >
        <View
          className="rounded-lg overflow-hidden"
          style={{
            width: 44,
            height: 44,
            backgroundColor: theme.bg,
            borderWidth: 1,
            borderColor: theme.textPlaceholder,
          }}
        >
          <Image
            source={{ uri: photoUri }}
            style={{ width: "100%", height: "100%" }}
            resizeMode="cover"
          />
        </View>
      </Pressable>

      <Modal
        visible={isPreviewOpen}
        transparent
        animationType="fade"
        onRequestClose={() => setIsPreviewOpen(false)}
      >
        <Pressable
          className="flex-1 justify-center items-center bg-black/80 px-6"
          onPress={() => setIsPreviewOpen(false)}
        >
          <Image
            source={{ uri: photoUri }}
            style={{
              width: 320,
              height: 320,
              borderRadius: 16,
            }}
            resizeMode="contain"
          />
        </Pressable>
      </Modal>
    </>
  );
}
