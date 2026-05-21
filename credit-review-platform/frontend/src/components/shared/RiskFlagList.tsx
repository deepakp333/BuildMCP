import type { RiskFlag } from "@/types";

const severityColors = {
  high: "border-red-600 bg-red-950/40 text-red-200",
  medium: "border-yellow-600 bg-yellow-950/40 text-yellow-200",
  low: "border-slate-600 bg-slate-800/40 text-slate-300",
};

export function RiskFlagList({ flags }: { flags: RiskFlag[] }) {
  if (!flags.length) {
    return <p className="text-sm text-slate-400">No risk flags triggered.</p>;
  }
  return (
    <ul className="space-y-2">
      {flags.map((f) => (
        <li
          key={f.code}
          className={`rounded-md border px-3 py-2 text-sm ${severityColors[f.severity]}`}
        >
          <span className="font-mono text-xs opacity-70">{f.code}</span>
          <p className="mt-0.5">{f.message}</p>
        </li>
      ))}
    </ul>
  );
}
