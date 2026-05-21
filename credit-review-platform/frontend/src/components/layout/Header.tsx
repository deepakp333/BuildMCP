import { Building2 } from "lucide-react";

export function Header() {
  return (
    <header className="border-b border-slate-700 bg-slate-900/80 px-6 py-4 backdrop-blur">
      <div className="flex items-center gap-3">
        <Building2 className="h-7 w-7 text-blue-500" />
        <div>
          <h1 className="text-xl font-bold tracking-tight">Credit Review Platform</h1>
          <p className="text-xs text-slate-400">
            Public &amp; private entity analysis with MCP-powered data extraction
          </p>
        </div>
      </div>
    </header>
  );
}
