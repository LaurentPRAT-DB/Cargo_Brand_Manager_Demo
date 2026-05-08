import { useState, useEffect } from "react";

interface Campaign {
  campaign_id: string;
  campaign_name: string;
  campaign_type: string;
  product_focus: string;
  target_segment: string;
  budget_usd: number;
  start_date: string;
  end_date: string;
}

interface ChannelAllocation {
  channel_name: string;
  allocation_pct: number;
  budget_usd: number;
  expected_roi: number;
  rationale: string;
}

interface Recommendation {
  allocations: ChannelAllocation[];
  total_expected_roi: number;
  summary: string;
}

export default function Campaigns() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [budget, setBudget] = useState("200000");
  const [segment, setSegment] = useState("Freight Forwarders");
  const [product, setProduct] = useState("All Products");
  const [duration, setDuration] = useState("3");
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [recommending, setRecommending] = useState(false);

  useEffect(() => {
    fetch("/api/campaigns")
      .then((r) => r.json())
      .then(setCampaigns)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  async function getRecommendation() {
    setRecommending(true);
    setRecommendation(null);
    try {
      const resp = await fetch("/api/campaigns/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          budget_usd: parseFloat(budget),
          target_segment: segment,
          product_focus: product,
          duration_months: parseInt(duration),
        }),
      });
      const data = await resp.json();
      setRecommendation(data);
    } catch (e: any) {
      setRecommendation({ allocations: [], total_expected_roi: 0, summary: `Error: ${e.message}` });
    } finally {
      setRecommending(false);
    }
  }

  return (
    <div className="p-8">
      <h2 className="text-2xl font-bold mb-6">Campaign Planner</h2>

      {/* Existing campaigns */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold mb-3">Active Campaigns</h3>
        {loading ? (
          <div className="h-32 bg-slate-100 animate-pulse rounded-lg" />
        ) : (
          <div className="overflow-x-auto border rounded-lg">
            <table className="w-full text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-3 py-2 text-left font-medium">Campaign</th>
                  <th className="px-3 py-2 text-left font-medium">Type</th>
                  <th className="px-3 py-2 text-left font-medium">Product</th>
                  <th className="px-3 py-2 text-left font-medium">Segment</th>
                  <th className="px-3 py-2 text-right font-medium">Budget</th>
                  <th className="px-3 py-2 text-left font-medium">Dates</th>
                </tr>
              </thead>
              <tbody>
                {campaigns.map((c) => (
                  <tr key={c.campaign_id} className="border-t">
                    <td className="px-3 py-2 font-medium">{c.campaign_name}</td>
                    <td className="px-3 py-2">{c.campaign_type}</td>
                    <td className="px-3 py-2">{c.product_focus}</td>
                    <td className="px-3 py-2">{c.target_segment}</td>
                    <td className="px-3 py-2 text-right">${c.budget_usd.toLocaleString()}</td>
                    <td className="px-3 py-2 text-xs">{c.start_date} → {c.end_date}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* New campaign recommendation */}
      <div className="border rounded-lg p-6 bg-white">
        <h3 className="text-lg font-semibold mb-4">Plan New Campaign</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Budget (USD)</label>
            <input
              type="number"
              value={budget}
              onChange={(e) => setBudget(e.target.value)}
              className="w-full border rounded px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Target Segment</label>
            <select value={segment} onChange={(e) => setSegment(e.target.value)} className="w-full border rounded px-3 py-2 text-sm">
              <option>Freight Forwarders</option>
              <option>Food & Pharma Exporters</option>
              <option>New Prospects</option>
              <option>Specialist Forwarders</option>
              <option>Trade Professionals</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Product Focus</label>
            <select value={product} onChange={(e) => setProduct(e.target.value)} className="w-full border rounded px-3 py-2 text-sm">
              <option>All Products</option>
              <option>Reefer Cargo</option>
              <option>Dry Container</option>
              <option>DG Cargo</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">Duration (months)</label>
            <select value={duration} onChange={(e) => setDuration(e.target.value)} className="w-full border rounded px-3 py-2 text-sm">
              <option value="1">1 month</option>
              <option value="2">2 months</option>
              <option value="3">3 months</option>
              <option value="6">6 months</option>
            </select>
          </div>
        </div>

        <button
          onClick={getRecommendation}
          disabled={recommending}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
        >
          {recommending ? "Analyzing..." : "Get AI Recommendation"}
        </button>

        {recommendation && (
          <div className="mt-6">
            <h4 className="font-medium mb-2">Recommended Channel Allocation</h4>
            {recommendation.allocations.length > 0 ? (
              <div className="space-y-3">
                {recommendation.allocations.map((a, i) => (
                  <div key={i} className="flex items-center gap-4 p-3 bg-slate-50 rounded">
                    <div className="w-32 font-medium text-sm">{a.channel_name}</div>
                    <div className="flex-1">
                      <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-blue-500 rounded-full"
                          style={{ width: `${a.allocation_pct}%` }}
                        />
                      </div>
                    </div>
                    <div className="text-sm text-right w-20">{a.allocation_pct}%</div>
                    <div className="text-sm text-right w-24">${a.budget_usd.toLocaleString()}</div>
                    <div className="text-sm text-right w-16 text-emerald-600">{a.expected_roi}x</div>
                  </div>
                ))}
                <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded text-sm">
                  <strong>Expected Total ROI:</strong> {recommendation.total_expected_roi}x
                  <p className="mt-1 text-slate-600">{recommendation.summary}</p>
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-500">{recommendation.summary}</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
