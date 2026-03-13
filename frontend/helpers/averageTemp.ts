export function averageTemp(
  highest: number | undefined,
  lowest: number | undefined,
): string {
  if (typeof highest !== "number" || typeof lowest !== "number") {
    return "Unknown";
  }
  return `${Math.round((highest + lowest) / 2)}°C`;
}
