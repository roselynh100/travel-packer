export function formatItemName(raw: string): string {
  const lower = raw.toLowerCase();
  const base = lower === "tops" ? "top" : lower;

  return base.charAt(0).toUpperCase() + base.slice(1);
}
