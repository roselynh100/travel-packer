import { useState } from "react";
import { Modal, Platform, Pressable } from "react-native";
import { ThemedText } from "@/components/ThemedText";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { useTheme } from "@/theme/useTheme";

type PackingListPillProps = {
  type: "weight" | "volume";
  value: number;
  max?: number;
};

// Used when trip does not provide max
const FALLBACK_CAPACITY = {
  weight: 23, // kg
  volume: 40000, // cm3
};

type PillStatus = "success" | "warning" | "error";

function convertToPercentFilled(value: number, max: number) {
  if (!Number.isFinite(max) || !Number.isFinite(value) || value <= 0) return 0;
  return value / max;
}

function statusFromPercentFilled(percentFilled: number): PillStatus {
  const remaining = 1 - percentFilled;
  if (remaining <= 0.25) return "error";
  if (remaining <= 0.5) return "warning";
  return "success";
}

export function PackingListPill({
  type,
  value,
  max: maxOverride,
}: PackingListPillProps) {
  const theme = useTheme();
  const [isTooltipOpen, setIsTooltipOpen] = useState(false);

  const max = maxOverride ?? FALLBACK_CAPACITY[type];
  const percentFilled = convertToPercentFilled(value, max);
  const status = statusFromPercentFilled(percentFilled);
  const colors = theme[status];

  const label = type === "weight" ? "Weight" : "Volume";
  const unit = type === "weight" ? "kg" : "cm³";

  const displayValue =
    type === "weight" ? value.toFixed(1) : Math.round(value).toString();
  const displayPercent = Math.round(percentFilled * 100);
  const text = `${label}: ${displayPercent}% used`;

  return (
    <>
      <Pressable
        onPress={() => setIsTooltipOpen(true)}
        className="rounded-full flex-row items-center border-2"
        style={{
          borderColor: colors.border,
          backgroundColor: colors.bg,
          paddingVertical: Platform.OS === "web" ? 10 : 6,
          paddingHorizontal: 12,
          gap: Platform.OS === "web" ? 8 : 4,
          alignSelf: "flex-start",
        }}
      >
        {Platform.OS === "web" && (
          <IconSymbol
            name={type === "weight" ? "gauge" : "cube.box.fill"}
            size={22}
            color={theme.text}
          />
        )}
        <ThemedText style={{ fontSize: 14 }}>{text}</ThemedText>
        <IconSymbol
          name="info.circle"
          size={18}
          color={theme.text}
          style={{ marginLeft: 2 }}
        />
      </Pressable>

      <Modal
        visible={isTooltipOpen}
        transparent
        animationType="fade"
        onRequestClose={() => setIsTooltipOpen(false)}
      >
        <Pressable
          className="flex-1 justify-center items-center bg-black/70"
          onPress={() => setIsTooltipOpen(false)}
        >
          <Pressable
            onPress={() => {}}
            className="rounded-2xl p-4"
            style={{
              backgroundColor: theme.bgNav,
              borderWidth: 1,
              borderColor: theme.textPlaceholder,
              width: "85%",
              maxWidth: 360,
            }}
          >
            <ThemedText type="defaultSemiBold">{label}</ThemedText>
            <ThemedText className="text-sm mt-2">
              Current {label.toLowerCase()}: {displayValue} {unit}
            </ThemedText>
            <ThemedText className="text-sm mt-1">
              Capacity: {max} {unit}
            </ThemedText>
          </Pressable>
        </Pressable>
      </Modal>
    </>
  );
}
