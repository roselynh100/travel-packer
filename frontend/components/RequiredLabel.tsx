import type { ReactNode } from "react";
import { ThemedText } from "@/components/ThemedText";

type RequiredLabelProps = {
  children: ReactNode;
};

export function RequiredLabel({ children }: RequiredLabelProps) {
  return (
    <ThemedText type="subtitle">
      {children}
      <ThemedText type="subtitle" className="text-red-500">
        {" "}
        *
      </ThemedText>
    </ThemedText>
  );
}
