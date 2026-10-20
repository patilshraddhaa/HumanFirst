import { useEffect, useMemo, useRef, useState } from "react";
import { BubbleMenu, EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";

// Standalone rich editor — not wired to a real draft ID.
// Uses local state only; persists nothing until integrated into the main flow.

const WORDS_PER_MINUTE = 200;
const AUTOSAVE_INTERVAL_MS = 30_000;
const PAUSE_THRESHOLD_MS = 2_000;

type SaveState = "idle" | "saving" | "saved" | "error";

type DraftMetrics = {
  keystrokes: number;
  pause_events: number;
  session_duration_seconds: number;
  paste_attempts: number;
};

type DraftDocument = {
  title: string;
  body: string;
  metrics: DraftMetrics;
  word_count: number;
  reading_time_minutes: number;
};

const EMPTY_METRICS: Required<DraftMetrics> = {
  keystrokes: 0,
  pause_events: 0,
  session_duration_seconds: 0,
  paste_attempts: 0,
};

function isTypingKey(event: KeyboardEvent) {
  if (event.metaKey || event.ctrlKey || event.altKey) {
    return false;
  }

  return (
    event.key.length === 1 ||
    event.key === "Backspace" ||
    event.key === "Delete" ||
    event.key === "Enter"
  );
}

function isPasteShortcut(event: KeyboardEvent) {
  return (
    ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "v") ||
    (event.shiftKey && event.key === "Insert")
  );
}

function countWords(text: string) {
  const trimmed = text.trim();
  if (!trimmed) {
    return 0;
  }

  return trimmed.split(/\s+/).length;
}

function formatReadingTime(words: number) {
  if (words === 0) {
    return "0 min read";
  }

  return `${Math.max(1, Math.ceil(words / WORDS_PER_MINUTE))} min read`;
}

function formatSavedAgo(lastSavedAt: Date | null, now: number) {
  if (!lastSavedAt) {
    return "Not saved yet";
  }

  const seconds = Math.max(0, Math.floor((now - lastSavedAt.getTime()) / 1000));
  if (seconds < 5) {
    return "Saved just now";
  }
  if (seconds < 60) {
    return `Saved ${seconds}s ago`;
  }

  const minutes = Math.floor(seconds / 60);
  return `Saved ${minutes}m ago`;
}

function normalizeMetrics(metrics?: DraftMetrics): Required<DraftMetrics> {
  return {
    keystrokes: metrics?.keystrokes ?? 0,
    pause_events: metrics?.pause_events ?? 0,
    session_duration_seconds: metrics?.session_duration_seconds ?? 0,
    paste_attempts: metrics?.paste_attempts ?? 0,
  };
}

function ToolbarButton({
  active,
  label,
  onClick,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] transition ${
        active
          ? "border-stone-900 bg-stone-900 text-stone-50"
          : "border-stone-300 bg-white/90 text-stone-700 hover:border-stone-500"
      }`}
      onMouseDown={(event) => {
        event.preventDefault();
        onClick();
      }}
    >
      {label}
    </button>
  );
}

// Stub hooks for the standalone editor (not wired to real draft ID)
function useLocalDraftData() {
  return { data: null as null | { title: string; body: string; metrics?: DraftMetrics; updated_at: Date }, isLoading: false };
}
function useLocalSaveDraft() {
  return {
    isPending: false,
    mutateAsync: async (payload: DraftDocument) => ({
      ...payload,
      updated_at: new Date(),
    }),
  };
}

export function WriteEditor() {
  const { data, isLoading } = useLocalDraftData();
  const saveDraft = useLocalSaveDraft();

  const [title, setTitle] = useState("");
  const [metrics, setMetrics] = useState<Required<DraftMetrics>>(EMPTY_METRICS);
  const [ghostMessage, setGhostMessage] = useState("");
  const [saveState, setSaveState] = useState<SaveState>("idle");
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null);
  const [now, setNow] = useState(() => Date.now());

  const hydratedRef = useRef(false);
  const dirtyRef = useRef(false);
  const pauseTimeoutRef = useRef<number | null>(null);
  const metricsBaseRef = useRef<Required<DraftMetrics>>(EMPTY_METRICS);
  const sessionStartRef = useRef(Date.now());
  const ghostTimeoutRef = useRef<number | null>(null);
  const titleRef = useRef("");
  const metricsRef = useRef<Required<DraftMetrics>>(EMPTY_METRICS);
  const wordCountRef = useRef(0);

  const showGhostMessage = () => {
    setGhostMessage("Typing only - paste is disabled...");
    if (ghostTimeoutRef.current) {
      window.clearTimeout(ghostTimeoutRef.current);
    }
    ghostTimeoutRef.current = window.setTimeout(
      () => setGhostMessage(""),
      1800,
    );
  };

  const markDirty = () => {
    dirtyRef.current = true;
  };

  const registerPause = () => {
    if (pauseTimeoutRef.current) {
      window.clearTimeout(pauseTimeoutRef.current);
    }
    pauseTimeoutRef.current = window.setTimeout(() => {
      setMetrics((current) => ({
        ...current,
        pause_events: current.pause_events + 1,
      }));
      markDirty();
    }, PAUSE_THRESHOLD_MS);
  };

  const registerKeystroke = () => {
    setMetrics((current) => ({
      ...current,
      keystrokes: current.keystrokes + 1,
    }));
    markDirty();
    registerPause();
  };

  const registerPasteAttempt = () => {
    setMetrics((current) => ({
      ...current,
      paste_attempts: current.paste_attempts + 1,
    }));
    markDirty();
    showGhostMessage();
  };

  const registerTitleChange = (previousTitle: string, nextTitle: string) => {
    if (previousTitle === nextTitle) {
      return;
    }

    setMetrics((current) => ({
      ...current,
      keystrokes:
        current.keystrokes +
        Math.max(1, Math.abs(nextTitle.length - previousTitle.length)),
    }));
    markDirty();
    registerPause();
  };

  const editor = useEditor({
    immediatelyRender: false,
    editorProps: {
      attributes: {
        class:
          "min-h-[360px] w-full max-w-none rounded-[2rem] border border-stone-200 bg-white/90 px-8 py-7 text-lg leading-8 text-stone-800 outline-none",
        spellcheck: "false",
      },
      handlePaste: () => {
        registerPasteAttempt();
        return true;
      },
      handleDrop: () => {
        registerPasteAttempt();
        return true;
      },
      handleDOMEvents: {
        keydown: (_, event) => {
          if (isPasteShortcut(event)) {
            event.preventDefault();
            registerPasteAttempt();
            return true;
          }

          if (isTypingKey(event)) {
            registerKeystroke();
          }
          return false;
        },
      },
    },
    extensions: [
      StarterKit.configure({
        blockquote: false,
        code: false,
        codeBlock: false,
        dropcursor: false,
        gapcursor: false,
        hardBreak: false,
        heading: { levels: [2, 3] },
        horizontalRule: false,
        strike: false,
      }),
    ],
    content: "",
    onUpdate: () => {
      markDirty();
    },
  });

  const bodyText = editor?.getText() ?? "";
  const wordCount = useMemo(
    () => countWords([title, bodyText].filter(Boolean).join(" ")),
    [bodyText, title],
  );
  const readingTimeLabel = useMemo(
    () => formatReadingTime(wordCount),
    [wordCount],
  );

  useEffect(() => {
    titleRef.current = title;
  }, [title]);

  useEffect(() => {
    metricsRef.current = metrics;
  }, [metrics]);

  useEffect(() => {
    wordCountRef.current = wordCount;
  }, [wordCount]);

  useEffect(() => {
    if (!data || !editor || hydratedRef.current) {
      return;
    }

    hydratedRef.current = true;
    setTitle(data.title ?? "");
    editor.commands.setContent(data.body ?? "", false);

    const nextMetrics = normalizeMetrics(data?.metrics);
    metricsBaseRef.current = nextMetrics;
    sessionStartRef.current = Date.now();
    setMetrics(nextMetrics);
    setLastSavedAt(data?.updated_at ?? null);
    setSaveState("saved");
  }, [data, editor]);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setNow(Date.now());
      setMetrics((current) => ({
        ...current,
        session_duration_seconds:
          metricsBaseRef.current.session_duration_seconds +
          Math.floor((Date.now() - sessionStartRef.current) / 1000),
      }));
    }, 1000);

    return () => window.clearInterval(timer);
  }, []);

  const buildPayload = (): DraftDocument => ({
    title: titleRef.current,
    body: editor?.getHTML() ?? "",
    metrics: metricsRef.current,
    word_count: wordCountRef.current,
    reading_time_minutes:
      wordCountRef.current === 0
        ? 0
        : Math.max(1, Math.ceil(wordCountRef.current / WORDS_PER_MINUTE)),
  });

  useEffect(() => {
    if (!editor || !hydratedRef.current) {
      return;
    }

    const timer = window.setInterval(async () => {
      if (!dirtyRef.current || saveDraft.isPending) {
        return;
      }

      setSaveState("saving");
      try {
        const response = await saveDraft.mutateAsync(buildPayload());
        const nextMetrics = normalizeMetrics(response.metrics);
        metricsBaseRef.current = nextMetrics;
        sessionStartRef.current = Date.now();
        setMetrics(nextMetrics);
        setLastSavedAt(response.updated_at instanceof Date ? response.updated_at : new Date(response.updated_at));
        setSaveState("saved");
        dirtyRef.current = false;
      } catch {
        setSaveState("error");
      }
    }, AUTOSAVE_INTERVAL_MS);

    return () => window.clearInterval(timer);
  }, [editor, saveDraft]);

  useEffect(() => {
    return () => {
      if (pauseTimeoutRef.current) {
        window.clearTimeout(pauseTimeoutRef.current);
      }
      if (ghostTimeoutRef.current) {
        window.clearTimeout(ghostTimeoutRef.current);
      }
    };
  }, []);

  const saveLabel =
    saveState === "saving"
      ? "Saving..."
      : saveState === "error"
        ? "Autosave failed"
        : formatSavedAgo(lastSavedAt, now);

  const cta =
    wordCount < 100
      ? { label: "Keep writing", disabled: true }
      : wordCount < 300
        ? { label: "Save draft", disabled: false }
        : { label: "Lock draft ->", disabled: false };

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(245,158,11,0.18),_transparent_30%),linear-gradient(180deg,_#f6f3ea_0%,_#efe7d8_48%,_#e7dbc6_100%)] px-4 py-8 text-stone-900 sm:px-6 lg:px-10">
      <section className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-6xl flex-col rounded-[2.5rem] border border-white/60 bg-white/55 p-5 shadow-[0_30px_80px_rgba(120,53,15,0.14)] backdrop-blur md:p-8">
        <header className="flex flex-col gap-5 border-b border-stone-200/80 pb-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.35em] text-amber-700">
              Atomic editor
            </p>
            <h1 className="mt-2 font-serif text-3xl leading-tight text-stone-900 md:text-4xl">
              Write without shortcuts
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-stone-600">
              Formatting is limited on purpose. Paste is blocked across the
              editor so the draft reflects live thinking, not imported text.
            </p>
          </div>
          <div className="rounded-full border border-stone-200 bg-white/85 px-4 py-2 text-sm font-medium text-stone-600">
            {saveLabel}
          </div>
        </header>

        <div className="grid flex-1 gap-6 pt-6 lg:grid-cols-[minmax(0,1fr)_18rem]">
          <div className="relative">
            <label className="sr-only" htmlFor="draft-title">
              Draft title
            </label>
            <input
              id="draft-title"
              type="text"
              value={title}
              spellCheck={false}
              placeholder="Untitled draft"
              className="mb-4 w-full border-none bg-transparent px-2 py-3 font-serif text-4xl leading-tight text-stone-900 outline-none placeholder:text-stone-400"
              onChange={(event) => {
                const nextTitle = event.target.value;
                registerTitleChange(title, nextTitle);
                setTitle(nextTitle);
              }}
              onKeyDown={(event) => {
                if (isPasteShortcut(event.nativeEvent)) {
                  event.preventDefault();
                  registerPasteAttempt();
                  return;
                }
              }}
              onPaste={(event) => {
                event.preventDefault();
                registerPasteAttempt();
              }}
              onDrop={(event) => {
                event.preventDefault();
                registerPasteAttempt();
              }}
            />

            <div className="relative">
              {editor ? (
                <>
                  <BubbleMenu
                    editor={editor}
                    tippyOptions={{ duration: 150 }}
                    className="flex gap-2 rounded-full border border-stone-200 bg-[#f7f1e4] p-2 shadow-lg"
                  >
                    <ToolbarButton
                      active={editor.isActive("bold")}
                      label="Bold"
                      onClick={() => editor.chain().focus().toggleBold().run()}
                    />
                    <ToolbarButton
                      active={editor.isActive("italic")}
                      label="Italic"
                      onClick={() =>
                        editor.chain().focus().toggleItalic().run()
                      }
                    />
                    <ToolbarButton
                      active={editor.isActive("heading", { level: 2 })}
                      label="H2"
                      onClick={() =>
                        editor.chain().focus().toggleHeading({ level: 2 }).run()
                      }
                    />
                    <ToolbarButton
                      active={editor.isActive("heading", { level: 3 })}
                      label="H3"
                      onClick={() =>
                        editor.chain().focus().toggleHeading({ level: 3 }).run()
                      }
                    />
                    <ToolbarButton
                      active={editor.isActive("bulletList")}
                      label="Bullets"
                      onClick={() =>
                        editor.chain().focus().toggleBulletList().run()
                      }
                    />
                    <ToolbarButton
                      active={editor.isActive("orderedList")}
                      label="Numbers"
                      onClick={() =>
                        editor.chain().focus().toggleOrderedList().run()
                      }
                    />
                  </BubbleMenu>
                  <EditorContent editor={editor} />
                </>
              ) : (
                <div className="min-h-[360px] animate-pulse rounded-[2rem] border border-stone-200 bg-white/80" />
              )}

              {ghostMessage ? (
                <div className="pointer-events-none absolute inset-x-6 top-6 rounded-2xl border border-amber-300/70 bg-amber-50/95 px-4 py-3 text-sm font-medium text-amber-900 shadow-[0_15px_30px_rgba(245,158,11,0.18)] animate-[ghost-fade_1.8s_ease-out]">
                  {ghostMessage}
                </div>
              ) : null}
            </div>
          </div>

          <aside className="flex flex-col justify-between rounded-[2rem] border border-stone-200 bg-[#fcfaf5] p-5">
            <div className="space-y-5">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.28em] text-stone-500">
                  Session metrics
                </p>
                <dl className="mt-4 space-y-3 text-sm text-stone-600">
                  <div className="flex items-center justify-between gap-3">
                    <dt>Keystrokes</dt>
                    <dd className="font-semibold text-stone-900">
                      {metrics.keystrokes}
                    </dd>
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <dt>Pause events</dt>
                    <dd className="font-semibold text-stone-900">
                      {metrics.pause_events}
                    </dd>
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <dt>Session time</dt>
                    <dd className="font-semibold text-stone-900">
                      {Math.floor(metrics.session_duration_seconds / 60)}m{" "}
                      {metrics.session_duration_seconds % 60}s
                    </dd>
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <dt>Paste attempts</dt>
                    <dd className="font-semibold text-stone-900">
                      {metrics.paste_attempts}
                    </dd>
                  </div>
                </dl>
              </div>

              <div className="rounded-[1.5rem] bg-stone-900 px-4 py-5 text-stone-50">
                <p className="text-xs font-semibold uppercase tracking-[0.28em] text-stone-300">
                  Threshold gate
                </p>
                <p className="mt-3 text-sm leading-6 text-stone-300">
                  Drafts under 100 words cannot advance. Between 100 and 299
                  words the CTA remains a save action. At 300 words the draft
                  can lock.
                </p>
              </div>
            </div>

            <button
              type="button"
              disabled={cta.disabled}
              className={`mt-6 rounded-full px-5 py-3 text-sm font-semibold uppercase tracking-[0.24em] transition ${
                cta.disabled
                  ? "cursor-not-allowed bg-stone-200 text-stone-500"
                  : "bg-amber-500 text-stone-950 shadow-[0_16px_30px_rgba(245,158,11,0.34)] hover:bg-amber-400"
              }`}
            >
              {cta.label}
            </button>
          </aside>
        </div>

        <footer className="mt-6 flex flex-col gap-3 border-t border-stone-200/80 pt-5 text-sm text-stone-600 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-5">
            <span>{wordCount} words</span>
            <span>{readingTimeLabel}</span>
          </div>
          <div className="text-xs uppercase tracking-[0.3em] text-stone-500">
            {isLoading ? "Loading draft" : "Spellcheck off"}
          </div>
        </footer>
      </section>
    </main>
  );
}
