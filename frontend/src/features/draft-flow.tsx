import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Link, Navigate, useNavigate, useParams } from "react-router-dom";
import { useDraft, useFinalizeDraftLock } from "../api/drafts";

function formatElapsed(ms: number) {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

function countWords(text: string) {
  const trimmed = text.trim();
  return trimmed ? trimmed.split(/\s+/).length : 0;
}

function buildLockedRoute(draftId: string, status: string) {
  return status === "draft"
    ? `/drafts/${draftId}/preview`
    : `/drafts/${draftId}/preview`;
}

export function DraftHub() {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_#fef3c7,_transparent_28%),linear-gradient(160deg,_#f7f4ec_0%,_#dde7f5_48%,_#cdded6_100%)] px-6 py-10 text-stone-900">
      <section className="mx-auto flex min-h-[calc(100vh-5rem)] max-w-5xl flex-col justify-center gap-8">
        <div className="max-w-2xl">
          <p className="text-xs font-semibold uppercase tracking-[0.35em] text-stone-500">
            HumanFirst lock ceremony
          </p>
          <h1 className="mt-4 font-['Fraunces'] text-5xl leading-tight text-stone-900">
            Freeze the writing session without losing the session evidence.
          </h1>
          <p className="mt-4 max-w-xl text-base leading-7 text-stone-600">
            Write a draft, lock it, and watch it move through the MCP enrichment
            pipeline into a published post.
          </p>
        </div>
      </section>
    </main>
  );
}

export function DraftEditorPage() {
  const params = useParams();
  const navigate = useNavigate();
  const draftId = params.draftId;
  const { data, isLoading, isError } = useDraft(draftId);
  const finalizeLock = useFinalizeDraftLock(draftId);

  const [title, setTitle] = useState("");
  const [bodyText, setBodyText] = useState("");
  const [showOverlay, setShowOverlay] = useState(false);
  const [keystrokes, setKeystrokes] = useState(0);
  const [pasteAttempts, setPasteAttempts] = useState(0);
  const [elapsedMs, setElapsedMs] = useState(0);
  const sessionStartedAt = useRef<number>(Date.now());

  useEffect(() => {
    if (!data) return;
    setTitle(data.title ?? "");
    setBodyText(data.body);
    setKeystrokes(0);
    setPasteAttempts(0);
    setElapsedMs(0);
    sessionStartedAt.current = Date.now();
  }, [data?.id]);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setElapsedMs(Date.now() - sessionStartedAt.current);
    }, 1000);

    return () => window.clearInterval(timer);
  }, []);

  const metrics = useMemo(
    () => ({
      wordCount: countWords(bodyText),
      timeSpent: formatElapsed(elapsedMs),
      keystrokes,
      pasteAttempts,
    }),
    [bodyText, elapsedMs, keystrokes, pasteAttempts],
  );

  if (!draftId) {
    return <Navigate to="/" replace />;
  }

  if (isLoading) {
    return <DraftPageFrame>Loading draft…</DraftPageFrame>;
  }

  if (isError || !data) {
    return (
      <DraftPageFrame>
        <div className="rounded-[1.75rem] border border-rose-200 bg-white/80 p-8 text-rose-700">
          Draft unavailable.
        </div>
      </DraftPageFrame>
    );
  }

  if (data.locked_at) {
    return <Navigate to={buildLockedRoute(draftId, data.status)} replace />;
  }

  const hasUnsavedChanges =
    title !== (data.title ?? "") || bodyText !== data.body;

  return (
    <DraftPageFrame>
      <section className="grid gap-6 lg:grid-cols-[1.4fr_0.75fr]">
        <article className="rounded-[2rem] border border-stone-200 bg-white/90 p-8 shadow-[0_24px_80px_rgba(54,63,69,0.12)]">
          <div className="flex items-start justify-between gap-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.32em] text-stone-500">
                Draft {draftId.slice(0, 8)}…
              </p>
              <h1 className="mt-3 font-['Fraunces'] text-4xl leading-tight text-stone-900">
                Write until the lock ceremony is the only thing left.
              </h1>
            </div>
            <button
              type="button"
              onClick={() => setShowOverlay(true)}
              className="rounded-full bg-stone-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-stone-700"
            >
              Lock draft
            </button>
          </div>
          <label className="mt-8 block">
            <span className="text-xs font-semibold uppercase tracking-[0.28em] text-stone-500">
              Post title
            </span>
            <input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              className="mt-3 w-full rounded-2xl border border-stone-200 bg-stone-50 px-5 py-4 text-lg text-stone-900 outline-none transition focus:border-emerald-500"
            />
          </label>
          <label className="mt-6 block">
            <span className="text-xs font-semibold uppercase tracking-[0.28em] text-stone-500">
              Draft body
            </span>
            <textarea
              value={bodyText}
              onChange={(event) => setBodyText(event.target.value)}
              onKeyDown={(event) => {
                if (
                  event.key.length === 1 ||
                  ["Backspace", "Delete", "Enter", "Tab"].includes(event.key)
                ) {
                  setKeystrokes((current) => current + 1);
                }
              }}
              onPaste={() => setPasteAttempts((current) => current + 1)}
              className="mt-3 min-h-[26rem] w-full rounded-[1.75rem] border border-stone-200 bg-stone-50 px-5 py-5 text-base leading-7 text-stone-900 outline-none transition focus:border-emerald-500"
            />
          </label>
          <div className="mt-6 flex items-center justify-between text-sm text-stone-500">
            <span>Session metrics are computed live from this editor state.</span>
            <span>{hasUnsavedChanges ? "Unsaved local changes" : "In sync"}</span>
          </div>
        </article>
        <aside className="rounded-[2rem] border border-white/60 bg-stone-900 p-7 text-stone-100 shadow-[0_24px_80px_rgba(33,37,41,0.18)]">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-stone-400">
            Session snapshot
          </p>
          <MetricRow label="Words" value={String(metrics.wordCount)} />
          <MetricRow label="Time spent" value={metrics.timeSpent} />
          <MetricRow label="Keystrokes" value={String(metrics.keystrokes)} />
          <MetricRow
            label="Paste attempts"
            value={
              metrics.pasteAttempts > 0
                ? String(metrics.pasteAttempts)
                : "No paste detected"
            }
          />
          <div className="mt-8 rounded-[1.5rem] border border-white/10 bg-white/5 p-5 text-sm leading-6 text-stone-300">
            Once locked, this draft can no longer re-enter write mode. The
            redirect destination is based on the draft's setup state.
          </div>
        </aside>
      </section>
      <LockOverlay
        open={showOverlay}
        title={title}
        metrics={metrics}
        pending={finalizeLock.isPending}
        errorMessage={
          finalizeLock.isError
            ? "Lock failed. Refresh the draft state and try again."
            : null
        }
        onClose={() => {
          if (!finalizeLock.isPending) setShowOverlay(false);
        }}
        onContinue={async () => {
          const locked = await finalizeLock.mutateAsync({ title, body: bodyText });
          if (locked && draftId) {
            navigate(buildLockedRoute(draftId, locked.status), { replace: true });
          }
        }}
      />
    </DraftPageFrame>
  );
}

function DraftPageFrame(props: { children: ReactNode }) {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,_#e7f3ec,_transparent_26%),linear-gradient(165deg,_#f5efe3_0%,_#eef3f8_44%,_#dbe9e4_100%)] px-6 py-8 text-stone-900">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <Link
          to="/"
          className="text-sm font-semibold uppercase tracking-[0.28em] text-stone-500 transition hover:text-stone-900"
        >
          HumanFirst draft index
        </Link>
        {props.children}
      </div>
    </main>
  );
}

function MetricRow(props: { label: string; value: string }) {
  return (
    <div className="mt-7 flex items-end justify-between gap-4 border-b border-white/10 pb-4">
      <span className="text-sm uppercase tracking-[0.24em] text-stone-400">
        {props.label}
      </span>
      <span className="font-['Fraunces'] text-3xl text-white">{props.value}</span>
    </div>
  );
}

function LockOverlay(props: {
  open: boolean;
  title: string;
  metrics: {
    wordCount: number;
    timeSpent: string;
    keystrokes: number;
    pasteAttempts: number;
  };
  pending: boolean;
  errorMessage: string | null;
  onClose: () => void;
  onContinue: () => Promise<void>;
}) {
  if (!props.open) return null;

  return (
    <div className="overlay-fade fixed inset-0 z-50 flex items-center justify-center bg-stone-950/55 px-6 py-10 backdrop-blur-sm">
      <div className="w-full max-w-3xl rounded-[2.25rem] bg-white p-8 shadow-[0_40px_120px_rgba(15,23,42,0.3)] md:p-10">
        <p className="text-xs font-semibold uppercase tracking-[0.35em] text-stone-500">
          Lock ceremony
        </p>
        <h2 className="mt-4 font-['Fraunces'] text-4xl leading-tight text-stone-900">
          {props.title || "Untitled draft"}
        </h2>
        <p className="mt-4 max-w-2xl text-base leading-7 text-stone-600">
          This is the final write-mode checkpoint. Continue will persist the
          latest local draft state, lock the draft, and remove access to the
          editor.
        </p>
        <div className="mt-8 grid gap-4 rounded-[1.75rem] bg-stone-100 p-5 md:grid-cols-2">
          <OverlayMetric label="Word count" value={String(props.metrics.wordCount)} />
          <OverlayMetric label="Time spent" value={props.metrics.timeSpent} />
          <OverlayMetric label="Keystroke count" value={String(props.metrics.keystrokes)} />
          <OverlayMetric
            label="Paste attempts"
            value={
              props.metrics.pasteAttempts > 0
                ? String(props.metrics.pasteAttempts)
                : "No paste detected"
            }
          />
        </div>
        {props.errorMessage ? (
          <p className="mt-5 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {props.errorMessage}
          </p>
        ) : null}
        <div className="mt-8 flex flex-col-reverse gap-3 md:flex-row md:justify-between">
          <button
            type="button"
            onClick={props.onClose}
            disabled={props.pending}
            className="rounded-full border border-stone-300 px-5 py-3 text-sm font-semibold text-stone-700 transition hover:border-stone-900 hover:text-stone-900 disabled:cursor-not-allowed disabled:opacity-60"
          >
            ← Back to editing
          </button>
          <button
            type="button"
            onClick={() => void props.onContinue()}
            disabled={props.pending}
            className="rounded-full bg-emerald-700 px-5 py-3 text-sm font-semibold text-white transition hover:bg-emerald-600 disabled:cursor-not-allowed disabled:bg-emerald-400"
          >
            {props.pending ? "Locking…" : "Continue →"}
          </button>
        </div>
      </div>
    </div>
  );
}

function OverlayMetric(props: { label: string; value: string }) {
  return (
    <div className="rounded-[1.4rem] bg-white px-5 py-4 shadow-[inset_0_0_0_1px_rgba(120,113,108,0.1)]">
      <p className="text-xs font-semibold uppercase tracking-[0.28em] text-stone-500">
        {props.label}
      </p>
      <p className="mt-3 font-['Fraunces'] text-3xl text-stone-900">{props.value}</p>
    </div>
  );
}

export function DraftPreviewPage() {
  return <LockedDraftView mode="preview" />;
}

export function DraftSetupPage() {
  return <LockedDraftView mode="setup" />;
}

function LockedDraftView(props: { mode: "preview" | "setup" }) {
  const params = useParams();
  const draftId = params.draftId;
  const { data, isLoading, isError } = useDraft(draftId);

  if (!draftId) {
    return <Navigate to="/" replace />;
  }

  if (isLoading) {
    return <DraftPageFrame>Loading draft…</DraftPageFrame>;
  }

  if (isError || !data) {
    return <DraftPageFrame>Draft unavailable.</DraftPageFrame>;
  }

  if (!data.locked_at) {
    return <Navigate to={`/drafts/${draftId}/edit`} replace />;
  }

  const isSetup = props.mode === "setup";

  return (
    <DraftPageFrame>
      <section className="rounded-[2rem] border border-white/70 bg-white/85 p-8 shadow-[0_24px_80px_rgba(54,63,69,0.12)]">
        <p className="text-xs font-semibold uppercase tracking-[0.32em] text-stone-500">
          {isSetup ? "Locked → setup" : "Locked → preview"}
        </p>
        <h1 className="mt-4 font-['Fraunces'] text-5xl leading-tight text-stone-900">
          {data.title ?? "Untitled draft"}
        </h1>
        <p className="mt-4 max-w-2xl text-base leading-7 text-stone-600">
          {isSetup
            ? "This draft is locked and cannot re-enter write mode. Finish the MCP setup step before continuing."
            : "This draft is locked and now lives in preview-only mode."}
        </p>
        <div className="mt-8 rounded-[1.75rem] bg-stone-100 p-6">
          <p className="whitespace-pre-wrap text-base leading-7 text-stone-700">
            {data.body}
          </p>
        </div>
        <div className="mt-8 flex flex-wrap gap-3">
          {isSetup ? (
            <Link
              to={`/drafts/${draftId}/preview`}
              className="rounded-full bg-stone-900 px-5 py-3 text-sm font-semibold text-white"
            >
              Continue to preview
            </Link>
          ) : null}
          <Link
            to={`/drafts/${draftId}/edit`}
            className="rounded-full border border-stone-300 px-5 py-3 text-sm font-semibold text-stone-600"
          >
            Attempt write mode
          </Link>
        </div>
      </section>
    </DraftPageFrame>
  );
}
