"use client";

import { useCallback, useId, useRef, useState } from "react";

import { Badge } from "@/shared/components/ui/Badge";
import { Button } from "@/shared/components/ui/Button";
import { Card } from "@/shared/components/ui/Card";
import { Textarea } from "@/shared/components/ui/Textarea";
import { Spinner } from "@/shared/components/feedback/Spinner";

import {
  useFrameworkDelete,
  useFrameworkIngest,
  useFrameworkList,
  useFrameworkUpload,
} from "./hooks";

const inputClass =
  "w-full rounded-lg border border-zinc-700 bg-zinc-900/80 px-3 py-2 text-sm text-zinc-100 outline-none " +
  "ring-emerald-500/30 placeholder:text-zinc-500 focus:ring-2";

type IngestTab = "paste" | "upload";

export function FrameworkLibrary() {
  const titleId = useId();
  const fwId = useId();
  const verId = useId();
  const jurId = useId();
  const uploadPasteId = useId();
  const [tab, setTab] = useState<IngestTab>("paste");
  const [title, setTitle] = useState("");
  const [framework, setFramework] = useState("Internal");
  const [version, setVersion] = useState("1.0");
  const [jurisdiction, setJurisdiction] = useState("EU");
  const [text, setText] = useState("");
  const [pasteExtra, setPasteExtra] = useState("");
  const [fileSelected, setFileSelected] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const fileId = useId();

  const list = useFrameworkList();
  const ingest = useFrameworkIngest();
  const upload = useFrameworkUpload();
  const del = useFrameworkDelete();

  const resetIngestForm = useCallback(() => {
    setTitle("");
    setFramework("Internal");
    setVersion("1.0");
    setJurisdiction("EU");
    setText("");
    setPasteExtra("");
    setFileSelected(false);
    if (fileRef.current) fileRef.current.value = "";
  }, []);

  const canPaste = title.trim() && framework.trim() && text.trim();
  const canUpload =
    title.trim() && framework.trim() && (fileSelected || pasteExtra.trim());

  const submitPaste = () => {
    if (!canPaste) return;
    ingest.mutate(
      {
        title: title.trim(),
        framework: framework.trim(),
        version: version.trim() || "1.0",
        jurisdiction: jurisdiction.trim() || undefined,
        text: text.trim(),
      },
      {
        onSuccess: () => {
          resetIngestForm();
          ingest.reset();
        },
      },
    );
  };

  const submitFile = () => {
    if (!title.trim() || !framework.trim()) return;
    const f = fileRef.current?.files?.[0];
    if (!f && !pasteExtra.trim()) return;
    const form = new FormData();
    form.set("title", title.trim());
    form.set("framework", framework.trim());
    form.set("version", version.trim() || "1.0");
    if (jurisdiction.trim()) form.set("jurisdiction", jurisdiction.trim());
    if (f) form.set("file", f);
    if (pasteExtra.trim()) form.set("paste", pasteExtra.trim());
    upload.mutate(form, {
      onSuccess: () => {
        resetIngestForm();
        upload.reset();
      },
    });
  };

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-8">
      <div className="space-y-2">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-50 md:text-3xl">
            Framework library
          </h1>
          <Badge tone="ok">RAG</Badge>
        </div>
        <p className="max-w-2xl text-sm leading-relaxed text-zinc-400">
          Add policy or control-framework text. We chunk, embed, and add it to the same index as
          seeded regulations so{" "}
          <code className="rounded border border-zinc-700/80 bg-zinc-900 px-1.5 py-0.5 text-[0.8rem] text-emerald-200/90">
            search_regulations
          </code>{" "}
          can retrieve it in the incident pipeline.
        </p>
      </div>

      <Card className="p-0 overflow-hidden">
        <div className="border-b border-zinc-800/90 bg-zinc-900/40 px-1 pt-1">
          <div
            className="flex gap-0.5 rounded-t-lg p-0.5"
            role="tablist"
            aria-label="How to add a document"
          >
            <button
              type="button"
              role="tab"
              id="framework-tab-paste"
              aria-selected={tab === "paste"}
              className={`relative min-h-[2.5rem] flex-1 rounded-md px-4 text-sm font-medium transition-colors ${
                tab === "paste"
                  ? "bg-zinc-800/90 text-zinc-50 shadow-sm ring-1 ring-zinc-700/80"
                  : "text-zinc-500 hover:bg-zinc-800/50 hover:text-zinc-300"
              }`}
              onClick={() => setTab("paste")}
            >
              <span className="flex items-center justify-center">Paste text</span>
              {tab === "paste" && (
                <span
                  className="absolute bottom-0 left-3 right-3 h-0.5 rounded-full bg-emerald-500/80"
                  aria-hidden
                />
              )}
            </button>
            <button
              type="button"
              role="tab"
              id="framework-tab-upload"
              aria-selected={tab === "upload"}
              className={`relative min-h-[2.5rem] flex-1 rounded-md px-4 text-sm font-medium transition-colors ${
                tab === "upload"
                  ? "bg-zinc-800/90 text-zinc-50 shadow-sm ring-1 ring-zinc-700/80"
                  : "text-zinc-500 hover:bg-zinc-800/50 hover:text-zinc-300"
              }`}
              onClick={() => setTab("upload")}
            >
              <span className="flex items-center justify-center">Upload file</span>
              {tab === "upload" && (
                <span
                  className="absolute bottom-0 left-3 right-3 h-0.5 rounded-full bg-emerald-500/80"
                  aria-hidden
                />
              )}
            </button>
          </div>
        </div>

        <div className="p-6 pt-5 space-y-6">
          <div>
            <h2 className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">
              Document metadata
            </h2>
            <p className="mb-4 mt-1 text-xs text-zinc-500">
              Used for both paths — how this library entry is labeled in retrieval.
            </p>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label
                  htmlFor={titleId}
                  className="mb-1.5 block text-xs font-medium text-zinc-400"
                >
                  Title
                </label>
                <input
                  id={titleId}
                  className={inputClass}
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. ACME IR Policy 2024"
                />
              </div>
              <div>
                <label
                  htmlFor={fwId}
                  className="mb-1.5 block text-xs font-medium text-zinc-400"
                >
                  Framework label
                </label>
                <input
                  id={fwId}
                  className={inputClass}
                  value={framework}
                  onChange={(e) => setFramework(e.target.value)}
                  placeholder="e.g. Internal, ISO-27001"
                />
              </div>
              <div>
                <label
                  htmlFor={verId}
                  className="mb-1.5 block text-xs font-medium text-zinc-400"
                >
                  Version
                </label>
                <input
                  id={verId}
                  className={inputClass}
                  value={version}
                  onChange={(e) => setVersion(e.target.value)}
                />
              </div>
              <div>
                <label
                  htmlFor={jurId}
                  className="mb-1.5 block text-xs font-medium text-zinc-400"
                >
                  Jurisdiction <span className="font-normal text-zinc-600">(optional)</span>
                </label>
                <input
                  id={jurId}
                  className={inputClass}
                  value={jurisdiction}
                  onChange={(e) => setJurisdiction(e.target.value)}
                  placeholder="EU, US, UK…"
                />
              </div>
            </div>
          </div>

          {tab === "paste" && (
            <div
              role="tabpanel"
              aria-labelledby="framework-tab-paste"
              className="space-y-3 border-t border-zinc-800/80 pt-6"
            >
              <div>
                <h2 className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">
                  Full text
                </h2>
                <p className="mb-3 mt-1 text-xs text-zinc-500">Paste the complete body to chunk and index.</p>
                <Textarea
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="Paste policy or framework text here…"
                  className="min-h-[220px] font-mono text-xs leading-relaxed"
                />
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <Button
                  disabled={!canPaste || ingest.isPending}
                  onClick={submitPaste}
                >
                  {ingest.isPending ? "Indexing…" : "Index pasted text"}
                </Button>
                {ingest.isError && (
                  <p className="text-sm text-rose-400">{(ingest.error as Error).message}</p>
                )}
                {ingest.isSuccess && !ingest.isPending && (
                  <p className="text-sm text-emerald-400/90">Saved — see list below.</p>
                )}
              </div>
            </div>
          )}

          {tab === "upload" && (
            <div
              role="tabpanel"
              aria-labelledby="framework-tab-upload"
              className="space-y-4 border-t border-zinc-800/80 pt-6"
            >
              <div>
                <h2 className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">
                  File
                </h2>
                <p className="mb-3 mt-1 text-xs text-zinc-500">
                  PDF, DOCX, or plain text. You can also append with the field below.
                </p>
                <label
                  htmlFor={fileId}
                  className="group flex min-h-[120px] cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-zinc-700/90 bg-zinc-900/40 px-4 py-8 text-center transition-colors hover:border-zinc-600 hover:bg-zinc-900/70"
                >
                  <input
                    id={fileId}
                    ref={fileRef}
                    type="file"
                    accept=".pdf,.docx,.txt,application/pdf"
                    className="sr-only"
                    onChange={() => setFileSelected(!!fileRef.current?.files?.length)}
                  />
                  <span className="text-sm text-zinc-300">
                    {fileSelected && fileRef.current?.files?.[0]?.name
                      ? fileRef.current.files[0].name
                      : "Click to choose a file — or add text only in the next box"}
                  </span>
                  <span className="text-xs text-zinc-500">
                    Max ~12 MB · .pdf, .docx, .txt
                  </span>
                </label>
              </div>

              <div>
                <label
                  htmlFor={uploadPasteId}
                  className="mb-1.5 block text-xs font-medium text-zinc-400"
                >
                  Extra text <span className="font-normal text-zinc-600">(optional)</span>
                </label>
                <p className="mb-2 text-xs text-zinc-500">
                  Appends to extracted file content, or use alone if you only have paste.
                </p>
                <Textarea
                  id={uploadPasteId}
                  value={pasteExtra}
                  onChange={(e) => setPasteExtra(e.target.value)}
                  placeholder="Optional: paste additional sections here…"
                  className="min-h-[120px] font-mono text-xs"
                />
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <Button
                  disabled={!canUpload || upload.isPending}
                  onClick={submitFile}
                >
                  {upload.isPending ? "Uploading…" : "Index file / text"}
                </Button>
                {upload.isError && (
                  <p className="text-sm text-rose-400">{(upload.error as Error).message}</p>
                )}
                {upload.isSuccess && !upload.isPending && (
                  <p className="text-sm text-emerald-400/90">Saved — see list below.</p>
                )}
              </div>
            </div>
          )}
        </div>
      </Card>

      <Card>
        <div className="mb-1 flex items-center justify-between gap-2">
          <div>
            <h2 className="text-sm font-medium text-zinc-200">Your documents</h2>
            <p className="mt-0.5 text-xs text-zinc-500">Only your uploads; removable anytime.</p>
          </div>
          <Button variant="ghost" className="shrink-0 text-xs" onClick={() => list.refetch()}>
            Refresh
          </Button>
        </div>
        {list.isLoading && (
          <div className="pt-4">
            <Spinner label="Loading" />
          </div>
        )}
        {list.data && (
          <ul className="mt-4 max-h-[22rem] space-y-2 overflow-auto pr-1">
            {list.data.items.length === 0 && (
              <li className="rounded-lg border border-dashed border-zinc-800 bg-zinc-900/20 px-4 py-8 text-center text-sm text-zinc-500">
                No custom frameworks yet. Use the tabs above to add one.
              </li>
            )}
            {list.data.items.map((d) => (
              <li
                key={d.user_document_id}
                className="group flex flex-col gap-2 rounded-lg border border-zinc-800/90 bg-zinc-900/30 p-4 transition-colors hover:border-zinc-700 hover:bg-zinc-900/50 sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="min-w-0">
                  <div className="truncate text-sm font-medium text-zinc-200">
                    {d.source_document}
                  </div>
                  <div className="mt-0.5 font-mono text-[10px] text-zinc-500">
                    {d.user_document_id}
                  </div>
                  <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-zinc-500">
                    <span className="text-zinc-400">{d.framework}</span>
                    <span>v{d.version}</span>
                    <span>{d.jurisdiction ?? "—"}</span>
                    <span className="text-emerald-500/80">{d.chunk_count} chunks</span>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  className="shrink-0 border border-rose-500/20 text-rose-300 hover:border-rose-500/40 hover:bg-rose-950/30"
                  disabled={del.isPending}
                  onClick={() => del.mutate(d.user_document_id)}
                >
                  Remove
                </Button>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
