import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

export function CallReportPanel({ callReport }: { callReport: Record<string, unknown> }) {
  const inst = (callReport.institution as Record<string, unknown>) || {};
  const ffiec = (callReport.ffiec_summary as Record<string, unknown>) || {};
  const name = inst.NAME ? String(inst.NAME) : null;
  const cert = callReport.cert ? String(callReport.cert) : null;
  const charter = callReport.charter ? String(callReport.charter) : null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">
          Call Report — {String(callReport.source || "FDIC/NCUA")}
        </CardTitle>
      </CardHeader>
      <CardContent className="text-sm space-y-2 text-slate-300">
        {name && <p>Institution: <span className="text-white">{name}</span></p>}
        {cert && <p>Cert: <span className="font-mono">{cert}</span></p>}
        {charter && <p>Charter: <span className="font-mono">{charter}</span></p>}
        {ffiec.tier1_capital_ratio != null && (
          <p>Tier 1 Capital: <span className="text-white">{String(ffiec.tier1_capital_ratio)}%</span></p>
        )}
        {ffiec.total_rbc_ratio != null && (
          <p>Total RBC: <span className="text-white">{String(ffiec.total_rbc_ratio)}%</span></p>
        )}
        {ffiec.liquidity_coverage != null && (
          <p>Liquidity Coverage: <span className="text-white">{String(ffiec.liquidity_coverage)}%</span></p>
        )}
      </CardContent>
    </Card>
  );
}
