export type EntityType = "public" | "private";
export type Signal = "strong" | "adequate" | "watch" | "weak";

export interface ResolvedEntity {
  id: string;
  name: string;
  entity_type: EntityType;
  ticker?: string | null;
  cik?: string | null;
  cert_number?: string | null;
  charter_number?: string | null;
  match_score: number;
}

export interface MetricPoint {
  period: string;
  value: number;
}

export interface MetricSeries {
  key: string;
  label: string;
  unit: string;
  points: MetricPoint[];
  trend_slope?: number | null;
  trend_direction?: "up" | "down" | "flat" | null;
}

export interface RiskFlag {
  code: string;
  severity: "low" | "medium" | "high";
  message: string;
  metric_key?: string | null;
}

export interface CamelsScore {
  capital: number;
  asset_quality: number;
  management: number;
  earnings: number;
  liquidity: number;
  sensitivity: number;
  composite: number;
}

export interface FilingRecord {
  form_type: string;
  filed_date: string;
  accession_number: string;
  description: string;
  url?: string | null;
}

export interface NewsArticle {
  title: string;
  source: string;
  published_at: string;
  url: string;
  sentiment: "positive" | "neutral" | "negative";
}

export interface LitigationRecord {
  case_name: string;
  court: string;
  date_filed: string;
  docket_number: string;
  url?: string | null;
}

export interface TradeSignal {
  payment_index: number;
  delinquency_rate: number;
  trade_credit_rating: string;
  supplier_count: number;
}

export interface PublicReviewResult {
  entity: ResolvedEntity;
  signal: Signal;
  metrics: MetricSeries[];
  camels?: CamelsScore | null;
  risk_flags: RiskFlag[];
  filings: FilingRecord[];
  news: NewsArticle[];
  commentary: string;
}

export interface PrivateReviewResult {
  entity: ResolvedEntity;
  signal: Signal;
  metrics: MetricSeries[];
  camels: CamelsScore;
  risk_flags: RiskFlag[];
  call_report: Record<string, unknown>;
  trade_signals?: TradeSignal | null;
  litigation: LitigationRecord[];
  commentary: string;
}

export type ReviewResult = PublicReviewResult | PrivateReviewResult;

export interface ExcelEntityRow {
  name: string;
  entity_type: EntityType;
  ticker?: string | null;
  cert_number?: string | null;
  notes?: string | null;
}
