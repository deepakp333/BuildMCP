import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import type { FilingRecord } from "@/types";

export function FilingsPanel({ filings }: { filings: FilingRecord[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">SEC EDGAR Filings</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2 max-h-64 overflow-auto">
          {filings.map((f, i) => (
            <li key={i} className="rounded border border-slate-700 p-2 text-sm">
              <div className="flex justify-between">
                <span className="font-mono text-blue-400">{f.form_type}</span>
                <span className="text-slate-500 text-xs">{f.filed_date}</span>
              </div>
              <p className="text-slate-300 mt-1">{f.description}</p>
              {f.url && (
                <a
                  href={f.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs text-blue-500 hover:underline mt-1 inline-block"
                >
                  View filing
                </a>
              )}
            </li>
          ))}
          {!filings.length && <p className="text-slate-500 text-sm">No filings found.</p>}
        </ul>
      </CardContent>
    </Card>
  );
}
