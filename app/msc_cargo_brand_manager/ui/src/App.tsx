import { useState } from "react";
import Dashboard from "./pages/Dashboard";
import Chat from "./pages/Chat";
import Email from "./pages/Email";
import Campaigns from "./pages/Campaigns";

type Page = "dashboard" | "chat" | "email" | "campaigns";

const NAV_ITEMS: { id: Page; label: string; icon: string }[] = [
  { id: "dashboard", label: "KPI Dashboard", icon: "📊" },
  { id: "chat", label: "Ask Genie", icon: "💬" },
  { id: "email", label: "Email Composer", icon: "✉️" },
  { id: "campaigns", label: "Campaign Planner", icon: "🎯" },
];

export default function App() {
  const [page, setPage] = useState<Page>("dashboard");

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <nav className="w-64 bg-slate-900 text-white flex flex-col">
        <div className="p-4 border-b border-slate-700">
          <h1 className="text-lg font-bold">MSC Cargo</h1>
          <p className="text-xs text-slate-400">Brand Manager</p>
        </div>
        <ul className="flex-1 p-2 space-y-1">
          {NAV_ITEMS.map((item) => (
            <li key={item.id}>
              <button
                onClick={() => setPage(item.id)}
                className={`w-full text-left px-3 py-2 rounded-md text-sm flex items-center gap-2 transition-colors ${
                  page === item.id
                    ? "bg-slate-700 text-white"
                    : "text-slate-300 hover:bg-slate-800"
                }`}
              >
                <span>{item.icon}</span>
                {item.label}
              </button>
            </li>
          ))}
        </ul>
        <div className="p-4 border-t border-slate-700 text-xs text-slate-500">
          v0.1.0 — Powered by Databricks
        </div>
      </nav>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        {page === "dashboard" && <Dashboard onAskGenie={(q) => { setPage("chat"); }} />}
        {page === "chat" && <Chat />}
        {page === "email" && <Email />}
        {page === "campaigns" && <Campaigns />}
      </main>
    </div>
  );
}
