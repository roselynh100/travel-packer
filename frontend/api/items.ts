import { apiFetch } from "@/constants/api";
import type { Item } from "@/constants/types";

export async function patchItemQuantity(
  itemId: string,
  quantity: number,
): Promise<Item> {
  const response = await apiFetch(`/items/${encodeURIComponent(itemId)}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ quantity }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(
      `API error (${response.status}): ${errorText || response.statusText}`,
    );
  }

  return response.json();
}

