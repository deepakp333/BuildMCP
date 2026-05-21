import { SignalBadge } from "../shared/SignalBadge";
import { MetricCard } from "../shared/MetricCard";
import { RiskFlagList } from "../shared/RiskFlagList";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { FilingsPanel } from "./FilingsPanel";
import { NewsPanel } from "./NewsPanel";
import type { PublicReviewResult } from "@/types";

export function PublicReviewCard({ review }: { review: PublicReviewResult }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">{review.entity.name}</h2>
        <SignalBadge signal={review.signal} />
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        {review.metrics.map((m) => (
          <MetricCard key={m.key} metric={m} />
        ))}
      </div>
      {review.camels && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">CAMELS Composite: {review.camels.composite.toFixed(1)}</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-3 gap-2 text-sm text-slate-300">
            <span>Capital: {review.camels.capital}</span>
            <span>Asset Quality: {review.camels.asset_quality}</span>
            <span>Earnings: {review.camels.earnings}</span>
            <span>Liquidity: {review.camels.liquidity}</span>
            <span>Sensitivity: {review.camels.sensitivity}</span>
            <span>Management: {review.camels.management}</span>
          </CardContent>
        </Card>
      )}
      <div className="grid md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Risk Flags</CardTitle>
          </CardHeader>
          <CardContent>
            <RiskFlagList flags={review.risk_flags} />
          </CardContent>
        </Card>
        <div className="space-y-4">
          <FilingsPanel filings={review.filings} />
          <NewsPanel news={review.news} />
        </div>
      </div>
    </div>
  );
}
