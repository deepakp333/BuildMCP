import { cn } from "@/lib/utils";
import type { Signal } from "@/types";

const styles: Record<Signal, string> = {
  strong: "bg-green-900/60 text-green-300 border-green-700",
  adequate: "bg-blue-900/60 text-blue-300 border-blue-700",
  watch: "bg-yellow-900/60 text-yellow-300 border-yellow-700",
  weak: "bg-red-900/60 text-red-300 border-red-700",
};

export function SignalBadge({ signal }: { signal: Signal }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-3 py-0.5 text-xs font-semibold uppercase tracking-wide",
        styles[signal]
      )}
    >
      {signal}
    </span>
  );
}
