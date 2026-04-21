"use client";

import { useMemo, useState } from "react";

import { analyzeBodySchema } from "@/Features/incidents/incidents.schema";
import { Badge } from "@/shared/components/ui/Badge";
import { Button } from "@/shared/components/ui/Button";
import { Card } from "@/shared/components/ui/Card";
import { Textarea } from "@/shared/components/ui/Textarea";
import { Spinner } from "@/shared/components/feedback/Spinner";

import {
  useAnalyzeIncident,
  useIncidentDetail,
  useIncidentList,
} from "./hooks";

function JsonPane({ value }: { value: unknown }) {
  const txt = JSON.stringify(value, null, 2);
  return (
    <pre className="max-h-[480px] overflow-auto rounded-lg border border-zinc-800 bg-black/40 p-4 font-mono text-[11px] leading-relaxed text-emerald-100/90">
      {txt}
    </pre>
  );
}

export function IncidentGovernance() {
  const [input, setInput] = useState("");
  const [jurisdiction, setJurisdiction] = useState<
    "EU" | "US-FED" | "UK" | "OTHER"
  >("EU");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const list = useIncidentList();
  const detail = useIncidentDetail(selectedId);
  const analyze = useAnalyzeIncident();

  const parsed = useMemo(() => analyzeBodySchema.safeParse({ raw_input: input, jurisdiction_hint: jurisdiction }), [input, jurisdiction]);

  const run = () => {
    const r = analyzeBodySchema.safeParse({ raw_input: input, jurisdiction_hint: jurisdiction });
    if (!r.success) return;
    analyze.mutate(r.data, {
      onSuccess: (data: unknown) => {
        const d = data as { incident_id?: string };
        if (d?.incident_id) setSelectedId(d.incident_id);
      },
    });
  };

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-8">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-50 md:text-3xl">
          Compliance governance engine
        </h1>
        <p className="max-w-3xl text-sm leading-relaxed text-zinc-400">
          Submit security logs or incident narratives. The orchestrator routes through Log
          Intelligence → RAG retrieval → Risk → Obligations → Escalation → Critic, with MCP tools
          for traceable actions — not a chatbot.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <div className="mb-4 flex flex-wrap items-center gap-2">
            <Badge tone="ok">Step 1</Badge>
            <span className="text-sm font-medium text-zinc-200">Incident intake</span>
          </div>
          <label className="mb-2 block text-xs uppercase tracking-wide text-zinc-500">
            Raw logs / narrative
          </label>
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Paste IAM trails, IDS alerts, ticket narrative, approximate record counts..."
          />
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs uppercase tracking-wide text-zinc-500">
                Jurisdiction hint
              </label>
              <select
                value={jurisdiction}
                onChange={(e) =>
                  setJurisdiction(e.target.value as typeof jurisdiction)
                }
                className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100"
              >
                <option value="EU">EU / EEA</option>
                <option value="US-FED">US Federal sector-style</option>
                <option value="UK">UK</option>
                <option value="OTHER">Other / multi</option>
              </select>
            </div>
            <div className="flex items-end">
              <Button
                className="w-full"
                disabled={!parsed.success || analyze.isPending}
                onClick={run}
              >
                Run governance pipeline
              </Button>
            </div>
          </div>
          {!parsed.success && input.length > 0 && (
            <p className="mt-2 text-xs text-rose-400">
              {parsed.error.issues[0]?.message}
            </p>
          )}
          {analyze.isPending && (
            <div className="mt-4">
              <Spinner label="Agents executing with MCP tools — may take a minute" />
            </div>
          )}
          {analyze.isError && (
            <p className="mt-4 text-sm text-rose-400">
              {(analyze.error as Error).message}
            </p>
          )}
          {analyze.isSuccess && (
            <div className="mt-4 space-y-2">
              <Badge tone="ok">Completed</Badge>
              <JsonPane value={analyze.data} />
            </div>
          )}
        </Card>

        <Card>
          <div className="mb-4 flex items-center justify-between gap-2">
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone="neutral">Registry</Badge>
              <span className="text-sm font-medium text-zinc-200">Stored cases</span>
            </div>
            <Button
              variant="ghost"
              className="text-xs"
              onClick={() => list.refetch()}
              disabled={list.isFetching}
            >
              Refresh
            </Button>
          </div>
          {list.isLoading && <Spinner label="Loading incidents" />}
          {list.data && (
            <div className="max-h-[420px] space-y-2 overflow-auto pr-1">
              {list.data.length === 0 && (
                <p className="text-sm text-zinc-500">No incidents yet.</p>
              )}
              {list.data.map((row) => (
                <button
                  key={row.id}
                  type="button"
                  onClick={() => setSelectedId(row.id)}
                  className={`w-full rounded-lg border px-3 py-2 text-left text-sm transition hover:bg-zinc-900 ${
                    selectedId === row.id
                      ? "border-emerald-600/80 bg-emerald-950/40"
                      : "border-zinc-800 bg-zinc-950/60"
                  }`}
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono text-[11px] text-zinc-500">{row.id.slice(0, 8)}…</span>
                    <Badge tone={row.regulator_notification_required ? "warn" : "neutral"}>
                      {row.incident_type ?? "pending"}
                    </Badge>
                    <span className="text-xs text-zinc-500">{row.status}</span>
                  </div>
                  <div className="mt-1 text-xs text-zinc-400">
                    Sev {row.severity_score ?? "—"} · Esc {row.escalation_level ?? "—"}
                  </div>
                </button>
              ))}
            </div>
          )}
        </Card>
      </div>

      {selectedId && (
        <Card>
          <div className="mb-4 flex flex-wrap items-center gap-2">
            <Badge tone="warn">Traceability</Badge>
            <span className="text-sm font-medium text-zinc-200">Selected case audit trail</span>
          </div>
          {detail.isLoading && <Spinner label="Loading detail" />}
          {detail.data && (
            <div className="grid gap-6 lg:grid-cols-2">
              <div>
                <h3 className="mb-2 text-xs uppercase tracking-wide text-zinc-500">
                  Incident record
                </h3>
                <JsonPane value={detail.data.incident} />
              </div>
              <div>
                <h3 className="mb-2 text-xs uppercase tracking-wide text-zinc-500">
                  Agent traces
                </h3>
                <div className="max-h-[420px] space-y-3 overflow-auto">
                  {detail.data.traces.map((t) => (
                    <div
                      key={`${t.agent_name}-${t.created_at}`}
                      className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-3 text-xs"
                    >
                      <div className="flex justify-between gap-2 text-[11px] text-zinc-400">
                        <span className="font-semibold text-emerald-300">{t.agent_name}</span>
                        <span>{t.latency_ms?.toFixed?.(0) ?? "—"} ms</span>
                      </div>
                      <p className="mt-2 line-clamp-6 whitespace-pre-wrap font-mono text-[10px] text-zinc-400">
                        {t.output_summary}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
