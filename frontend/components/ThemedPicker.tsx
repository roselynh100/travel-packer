import { cn } from "@/helpers/cn";
import { Picker, type PickerProps } from "@react-native-picker/picker";

export type ThemedPickerProps<T extends string> = PickerProps & {
  value: T;
  onChange: (value: T) => void;
  options: T[];
};

export function ThemedPicker<T extends string>({
  value,
  onChange,
  options,
}: ThemedPickerProps<T>) {
  const backgroundColor = "bg-[var(--color-bg-nav)]";

  const text = "text-sm font-400 text-[var(--color-text)]";

  const border = "border-2 border-[var(--color-text-placeholder)]";

  return (
    <Picker
      selectedValue={value}
      onValueChange={(v) => onChange(v as T)}
      className={cn("p-3 rounded-xl", backgroundColor, text, border)}
    >
      {options.map((opt) => (
        <Picker.Item key={opt} label={opt} value={opt} />
      ))}
    </Picker>
  );
}
