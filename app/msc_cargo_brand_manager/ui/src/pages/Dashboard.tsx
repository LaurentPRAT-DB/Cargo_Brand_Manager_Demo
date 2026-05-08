import { useState, useEffect } from "react";

interface KpiItem {
  name: string;
  value: number;
  target: number;
  alert_threshold: number;
  status: "green" | "amber" | "red";
  unit: string;
}

interface KpiSummary {
  kpis: KpiItem[];
  period: string;
}

const STATUS_COLORS = {
  green: { bg: "bg-emerald-50", border: "border-emerald-200", text: "text-emerald-700", dot: "bg-emerald-500" },
  amber: { bg: "bg-amber-50", border: "border-amber-200", text: "text-amber-700", dot: "bg-amber-500" },
  red: { bg: "bg-red-50", border: "border-red-200", text: "text-red-700", dot: "bg-red-500" },
};

function formatValue(value: number, unit: string): string {
  if (unit === "%") return `${value}%`;
  if (unit === "x") return `${value}x`;
  if (unit === "#") return value.toLocaleString();
  return value.toString();
}

export default function Dashboard({ onAskGenie }: { onAskGenie: (q: string) => void }) {
  const [data, setData] = useState<KpiSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/kpi/summary")
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="p-8">
        <h2 className="text-2xl font-bold mb-6">KPI Dashboard</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 9 }).map((_, i) => (
            <div key={i} className="h-32 bg-slate-100 animate-pulse rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <h2 className="text-2xl font-bold mb-4">KPI Dashboard</h2>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          Failed to load KPIs: {error}
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold">KPI Dashboard</h2>
          <p className="text-sm text-slate-500">Reporting period: {data?.period}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {data?.kpis.map((kpi) => {
          const colors = STATUS_COLORS[kpi.status];
          return (
            <button
              key={kpi.name}
              onClick={() => onAskGenie(`Why is ${kpi.name} at ${formatValue(kpi.value, kpi.unit)}?`)}
              className={`${colors.bg} ${colors.border} border rounded-lg p-4 text-left hover:shadow-md transition-shadow cursor-pointer`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-600">{kpi.name}</span>
                <span className={`w-2.5 h-2.5 rounded-full ${colors.dot}`} />
              </div>
              <div className={`text-2xl font-bold ${colors.text}`}>
                {formatValue(kpi.value, kpi.unit)}
              </div>
              <div className="text-xs text-slate-500 mt-1">
                Target: {formatValue(kpi.target, kpi.unit)} | Alert: &lt;{formatValue(kpi.alert_threshold, kpi.unit)}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
