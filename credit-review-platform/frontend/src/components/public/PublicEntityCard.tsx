import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import type { ResolvedEntity } from "@/types";

export function PublicEntityCard({ entity }: { entity: ResolvedEntity }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{entity.name}</CardTitle>
      </CardHeader>
      <CardContent className="text-sm text-slate-400 space-y-1">
        {entity.ticker && <p>Ticker: <span className="text-white font-mono">{entity.ticker}</span></p>}
        {entity.cik && <p>CIK: <span className="text-white font-mono">{entity.cik}</span></p>}
        <p>Match: <span className="text-white">{entity.match_score.toFixed(0)}%</span></p>
      </CardContent>
    </Card>
  );
}
