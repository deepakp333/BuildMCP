import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import type { LitigationRecord } from "@/types";

export function LitigationPanel({ cases }: { cases: LitigationRecord[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Litigation ({cases.length})</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2 max-h-48 overflow-auto text-sm">
          {cases.map((c, i) => (
            <li key={i} className="border-b border-slate-700 pb-2">
              <p className="font-medium text-slate-200">{c.case_name}</p>
              <p className="text-xs text-slate-500">{c.court} — {c.date_filed}</p>
              <p className="text-xs font-mono text-slate-400">{c.docket_number}</p>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
