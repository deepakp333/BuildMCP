import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import type { TradeSignal } from "@/types";

export function TradeSignalPanel({ signals }: { signals: TradeSignal }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Trade &amp; Payment Signals</CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <p className="text-slate-500">Payment Index</p>
          <p className="text-xl font-bold text-white">{signals.payment_index.toFixed(0)}</p>
        </div>
        <div>
          <p className="text-slate-500">Delinquency Rate</p>
          <p className="text-xl font-bold text-white">{signals.delinquency_rate.toFixed(1)}%</p>
        </div>
        <div>
          <p className="text-slate-500">Trade Credit Rating</p>
          <p className="text-xl font-bold text-blue-400">{signals.trade_credit_rating}</p>
        </div>
        <div>
          <p className="text-slate-500">Supplier Count</p>
          <p className="text-xl font-bold text-white">{signals.supplier_count}</p>
        </div>
      </CardContent>
    </Card>
  );
}
