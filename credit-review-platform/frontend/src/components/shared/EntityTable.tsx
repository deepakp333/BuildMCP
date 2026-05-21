import * as Checkbox from "@radix-ui/react-checkbox";
import { Check } from "lucide-react";
import type { ExcelEntityRow } from "@/types";

export function EntityTable({
  entities,
  selected,
  onToggle,
}: {
  entities: ExcelEntityRow[];
  selected: Set<number>;
  onToggle: (index: number) => void;
}) {
  if (!entities.length) return null;

  return (
    <div className="overflow-auto rounded-md border border-slate-700">
      <table className="w-full text-sm">
        <thead className="bg-slate-800 text-left text-slate-400">
          <tr>
            <th className="p-2 w-8"></th>
            <th className="p-2">Name</th>
            <th className="p-2">Type</th>
            <th className="p-2">Ticker/Cert</th>
          </tr>
        </thead>
        <tbody>
          {entities.map((e, i) => (
            <tr key={i} className="border-t border-slate-700 hover:bg-slate-800/50">
              <td className="p-2">
                <Checkbox.Root
                  checked={selected.has(i)}
                  onCheckedChange={() => onToggle(i)}
                  className="flex h-4 w-4 items-center justify-center rounded border border-slate-500 data-[state=checked]:bg-blue-600"
                >
                  <Checkbox.Indicator>
                    <Check className="h-3 w-3 text-white" />
                  </Checkbox.Indicator>
                </Checkbox.Root>
              </td>
              <td className="p-2 font-medium">{e.name}</td>
              <td className="p-2 capitalize text-slate-400">{e.entity_type}</td>
              <td className="p-2 text-slate-400">{e.ticker || e.cert_number || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
