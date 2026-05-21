import { Line, LineChart, ResponsiveContainer, Tooltip } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import type { MetricSeries } from "@/types";

export function MetricCard({ metric }: { metric: MetricSeries }) {
  const data = metric.points.map((p) => ({ period: p.period, value: p.value }));
  const latest = metric.points[metric.points.length - 1]?.value ?? 0;
  const trendColor =
    metric.trend_direction === "up"
      ? "text-green-400"
      : metric.trend_direction === "down"
        ? "text-red-400"
        : "text-slate-400";

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-slate-300">{metric.label}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-baseline justify-between">
          <span className="text-2xl font-bold">
            {latest.toFixed(2)}
            <span className="text-sm font-normal text-slate-400">{metric.unit}</span>
          </span>
          {metric.trend_direction && (
            <span className={`text-xs ${trendColor}`}>↑↓ {metric.trend_direction}</span>
          )}
        </div>
        <div className="h-16 mt-2">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} dot={false} />
              <Tooltip
                contentStyle={{ background: "#1e293b", border: "1px solid #334155" }}
                labelStyle={{ color: "#94a3b8" }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
