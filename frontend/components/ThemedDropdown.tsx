import { useState } from "react";
import DropDownPicker from "react-native-dropdown-picker";

export type ThemedDropdownProps<T extends string> = {
  value: T | null;
  onChange: (v: T) => void;
  options: T[];
};

export function ThemedDropdown<T extends string>({
  value,
  onChange,
  options,
}: ThemedDropdownProps<T>) {
  const [open, setOpen] = useState(false);

  const items = options.map((opt) => ({ label: opt, value: opt }));

  return (
    <DropDownPicker
      open={open}
      value={value}
      items={items}
      setOpen={setOpen}
      setValue={(val) => onChange(val as unknown as T)}
      style={{
        borderRadius: 12,
        padding: 12,
        backgroundColor: "var(--color-bg-nav)",
        borderColor: "var(--color-text-placeholder)",
        borderWidth: 2,
      }}
      dropDownContainerStyle={{
        backgroundColor: "var(--color-bg-nav)",
        borderColor: "var(--color-text-placeholder)",
        borderLeftWidth: 2,
        borderRightWidth: 2,
        borderBottomWidth: 2,
      }}
      listItemContainerStyle={{
        backgroundColor: "var(--color-bg-nav)",
      }}
      textStyle={{
        color: "var(--color-text)",
      }}
      placeholder="Select..."
    />
  );
}
