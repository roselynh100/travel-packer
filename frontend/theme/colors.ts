/**
 * Single source of truth for app colors. Used on web and mobile
 * (CSS variables are not supported in React Native).
 */
export const colors = {
  light: {
    bg: "#ffffff",
    bgNav: "#f5f5f5",
    text: "#000000",
    textPlaceholder: "#cfcfcf",
    primary: "#00c3d0",
    tabSelected: "#2eb2bb",
    selectedItemBg: "rgba(0, 195, 208, 0.25)",
  },
  dark: {
    bg: "#141414",
    bgNav: "#1d1d1d",
    text: "#e3e3e3",
    textPlaceholder: "#484848",
    primary: "#007a82",
    tabSelected: "#316064",
    selectedItemBg: "rgba(0, 122, 130, 0.35)",
  },
} as const;

export type ThemeColors = (typeof colors)["light"] | (typeof colors)["dark"];
