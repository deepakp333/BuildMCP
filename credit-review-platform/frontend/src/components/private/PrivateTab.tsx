import { Play } from "lucide-react";
import { Button } from "../ui/button";
import { EntitySearch } from "../shared/EntitySearch";
import { ExcelUploader } from "../shared/ExcelUploader";
import { CommentaryPanel } from "../shared/CommentaryPanel";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { PrivateReviewCard } from "./PrivateReviewCard";
import { useRunReview, useReviewPoll } from "@/hooks/useEntityReview";
import { useMCPStream } from "@/hooks/useMCPStream";
import { useReviewStore } from "@/store/reviewStore";

export function PrivateTab() {
  const store = useReviewStore();
  const runReview = useRunReview("private");
  const { runReviewWithStream } = useMCPStream();
  useReviewPoll(store.activeReviewId);

  const handleRun = () => {
    if (!store.selectedEntity) return;
    runReviewWithStream(store.selectedEntity, "private");
    runReview.mutate();
  };

  const entity = store.selectedEntity;

  return (
    <div className="grid lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 space-y-6">
        <section>
          <h2 className="text-sm font-semibold text-slate-400 mb-3">ENTITY RESOLUTION</h2>
          <EntitySearch entityType="private" />
          {entity && (
            <Card className="mt-4">
              <CardHeader>
                <CardTitle>{entity.name}</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-slate-400">
                {entity.cert_number && <p>FDIC Cert: {entity.cert_number}</p>}
                {entity.charter_number && <p>NCUA Charter: {entity.charter_number}</p>}
                <p>Match: {entity.match_score.toFixed(0)}%</p>
                <Button className="mt-3" onClick={handleRun} disabled={runReview.isPending || store.isStreaming}>
                  <Play className="h-4 w-4 mr-1" />
                  Run Private Credit Review
                </Button>
              </CardContent>
            </Card>
          )}
        </section>
        <section>
          <h2 className="text-sm font-semibold text-slate-400 mb-3">BATCH UPLOAD</h2>
          <ExcelUploader />
        </section>
        {store.privateReview && (
          <section>
            <h2 className="text-sm font-semibold text-slate-400 mb-3">REVIEW RESULTS</h2>
            <PrivateReviewCard review={store.privateReview} />
          </section>
        )}
      </div>
      <div>
        <CommentaryPanel commentary={store.commentary} isStreaming={store.isStreaming} />
      </div>
    </div>
  );
}
