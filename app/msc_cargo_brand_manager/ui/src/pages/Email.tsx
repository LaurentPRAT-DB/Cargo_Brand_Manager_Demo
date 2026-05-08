import { useState } from "react";

export default function Email() {
  const [recipient, setRecipient] = useState("");
  const [subject, setSubject] = useState("");
  const [context, setContext] = useState("");
  const [tone, setTone] = useState("professional");
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  async function generateDraft() {
    if (!recipient || !subject || !context) return;
    setLoading(true);
    setDraft("");
    try {
      const resp = await fetch("/api/email/draft", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ recipient, subject, context, tone }),
      });
      const data = await resp.json();
      setDraft(data.draft || "Failed to generate draft.");
    } catch (e: any) {
      setDraft(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  function copyToClipboard() {
    navigator.clipboard.writeText(draft);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="p-8 max-w-4xl">
      <h2 className="text-2xl font-bold mb-6">Email Composer</h2>
      <p className="text-sm text-slate-500 mb-6">
        Generate professional emails with data-driven insights from your KPI analysis.
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Form */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Recipient</label>
            <input
              type="text"
              value={recipient}
              onChange={(e) => setRecipient(e.target.value)}
              placeholder="e.g., Regional VP South Asia"
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Subject</label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="e.g., NPS Performance Review — Action Required"
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Tone</label>
            <select
              value={tone}
              onChange={(e) => setTone(e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="professional">Professional</option>
              <option value="urgent">Urgent</option>
              <option value="congratulatory">Congratulatory</option>
              <option value="executive-summary">Executive Summary</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Context / Data Points
            </label>
            <textarea
              value={context}
              onChange={(e) => setContext(e.target.value)}
              rows={6}
              placeholder="Paste KPI data or Genie insights here...&#10;e.g., NPS in South Asia dropped to 18 (target: 35). Top negative driver: documentation complexity. EMEA performing well at 38."
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <button
            onClick={generateDraft}
            disabled={loading || !recipient || !subject || !context}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Generating..." : "Generate Draft"}
          </button>
        </div>

        {/* Preview */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium text-slate-700">Email Preview</label>
            {draft && (
              <button
                onClick={copyToClipboard}
                className="text-xs px-2 py-1 border rounded hover:bg-slate-50"
              >
                {copied ? "Copied!" : "Copy"}
              </button>
            )}
          </div>
          <div className="border rounded-lg p-4 min-h-[300px] bg-white">
            {draft ? (
              <div className="text-sm whitespace-pre-wrap text-slate-700">{draft}</div>
            ) : (
              <p className="text-sm text-slate-400 italic">
                Your generated email will appear here...
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
