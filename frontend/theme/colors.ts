export const colors = {
  light: {
    bg: "#ffffff",
    bgNav: "#f5f5f5",
    text: "#000000",
    textPlaceholder: "#cfcfcf",
    primary: "#00c3d0",
    tabSelected: "#2eb2bb",
    selectedItemBg: "rgba(0, 195, 208, 0.25)",
    success: {
      bg: "#CDF4D3",
      border: "#66D575",
    },
    warning: {
      bg: "#FFECBD",
      border: "#FFC943",
    },
    error: {
      bg: "#FFC7C2",
      border: "#F24822",
    },
  },
  dark: {
    bg: "#141414",
    bgNav: "#1d1d1d",
    text: "#e3e3e3",
    textPlaceholder: "#484848",
    primary: "#007a82",
    tabSelected: "#316064",
    selectedItemBg: "rgba(0, 122, 130, 0.35)",
    success: {
      bg: "#11771f",
      border: "#096715",
    },
    warning: {
      bg: "#c88f00",
      border: "#b68300",
    },
    error: {
      bg: "#a42a0f",
      border: "#8d250e",
    },
  },
} as const;

export type ThemeColors = (typeof colors)["light"] | (typeof colors)["dark"];
