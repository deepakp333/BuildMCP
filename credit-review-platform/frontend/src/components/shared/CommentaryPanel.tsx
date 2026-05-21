import { useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

export function CommentaryPanel({
  commentary,
  isStreaming,
}: {
  commentary: string;
  isStreaming?: boolean;
}) {
  const ref = useRef<HTMLPreElement>(null);

  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [commentary]);

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Credit Commentary
          {isStreaming && (
            <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-blue-500" />
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <pre
          ref={ref}
          className="max-h-96 overflow-auto whitespace-pre-wrap font-mono text-xs leading-relaxed text-slate-300"
        >
          {commentary || "Commentary will stream here during review..."}
        </pre>
      </CardContent>
    </Card>
  );
}
