import { FileSpreadsheet, Globe, Lock } from "lucide-react";

export function Sidebar() {
  return (
    <aside className="w-56 shrink-0 border-r border-slate-700 bg-slate-900/50 p-4 hidden lg:block">
      <nav className="space-y-4 text-sm">
        <div>
          <p className="text-xs font-semibold uppercase text-slate-500 mb-2">Entity Types</p>
          <ul className="space-y-2 text-slate-300">
            <li className="flex items-center gap-2">
              <Globe className="h-4 w-4 text-blue-400" />
              Public (SEC EDGAR)
            </li>
            <li className="flex items-center gap-2">
              <Lock className="h-4 w-4 text-purple-400" />
              Private (FDIC/NCUA)
            </li>
          </ul>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase text-slate-500 mb-2">Data Sources</p>
          <ul className="space-y-1 text-xs text-slate-400">
            <li>FDIC BankFind</li>
            <li>FFIEC CDR</li>
            <li>NCUA Call Reports</li>
            <li>SEC EDGAR</li>
            <li>NewsAPI</li>
            <li>CourtListener</li>
          </ul>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-500 pt-4 border-t border-slate-700">
          <FileSpreadsheet className="h-4 w-4" />
          Batch Excel upload
        </div>
      </nav>
    </aside>
  );
}
