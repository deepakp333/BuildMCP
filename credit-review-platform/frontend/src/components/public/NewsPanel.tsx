import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import type { NewsArticle } from "@/types";

const sentimentStyle = {
  positive: "text-green-400",
  negative: "text-red-400",
  neutral: "text-slate-400",
};

export function NewsPanel({ news }: { news: NewsArticle[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">News &amp; Sentiment</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2 max-h-64 overflow-auto">
          {news.map((a, i) => (
            <li key={i} className="border-b border-slate-700 pb-2 text-sm last:border-0">
              <p className="font-medium text-slate-200">{a.title}</p>
              <div className="flex justify-between mt-1 text-xs">
                <span className="text-slate-500">{a.source}</span>
                <span className={sentimentStyle[a.sentiment]}>{a.sentiment}</span>
              </div>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
