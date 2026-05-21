import { Play } from "lucide-react";
import { Button } from "../ui/button";
import { EntitySearch } from "../shared/EntitySearch";
import { ExcelUploader } from "../shared/ExcelUploader";
import { CommentaryPanel } from "../shared/CommentaryPanel";
import { PublicEntityCard } from "./PublicEntityCard";
import { PublicReviewCard } from "./PublicReviewCard";
import { useRunReview, useReviewPoll } from "@/hooks/useEntityReview";
import { useMCPStream } from "@/hooks/useMCPStream";
import { useReviewStore } from "@/store/reviewStore";

export function PublicTab() {
  const store = useReviewStore();
  const runReview = useRunReview("public");
  const { runReviewWithStream } = useMCPStream();
  useReviewPoll(store.activeReviewId);

  const handleRun = () => {
    if (!store.selectedEntity) return;
    runReviewWithStream(store.selectedEntity, "public");
    runReview.mutate();
  };

  return (
    <div className="grid lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 space-y-6">
        <section>
          <h2 className="text-sm font-semibold text-slate-400 mb-3">ENTITY RESOLUTION</h2>
          <EntitySearch entityType="public" />
          {store.selectedEntity && (
            <div className="mt-4">
              <PublicEntityCard entity={store.selectedEntity} />
              <Button className="mt-3" onClick={handleRun} disabled={runReview.isPending || store.isStreaming}>
                <Play className="h-4 w-4 mr-1" />
                Run Public Credit Review
              </Button>
            </div>
          )}
        </section>
        <section>
          <h2 className="text-sm font-semibold text-slate-400 mb-3">BATCH UPLOAD</h2>
          <ExcelUploader />
        </section>
        {store.publicReview && (
          <section>
            <h2 className="text-sm font-semibold text-slate-400 mb-3">REVIEW RESULTS</h2>
            <PublicReviewCard review={store.publicReview} />
          </section>
        )}
      </div>
      <div>
        <CommentaryPanel commentary={store.commentary} isStreaming={store.isStreaming} />
      </div>
    </div>
  );
}
