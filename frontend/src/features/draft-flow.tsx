import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link, Navigate, useNavigate, useParams } from "react-router-dom";
import { ArrowRight, LockKeyhole, Save } from "lucide-react";

import { useDraft, useFinalizeDraftLock, useUpdateDraft } from "../api/drafts";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { Badge } from "../components/ui/badge";

function wordCount(value: string) {
  return value.trim() ? value.trim().split(/\s+/).length : 0;
}

export function DraftEditorPage() {
  const { draftId = "" } = useParams();
  const navigate = useNavigate();
  const draft = useDraft(draftId);
  const save = useUpdateDraft(draftId);
  const lock = useFinalizeDraftLock(draftId);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [ready, setReady] = useState(false);
  const [showLock, setShowLock] = useState(false);

  useEffect(() => {
    if (!draft.data || ready) return;
    setTitle(draft.data.title ?? "");
    setBody(draft.data.body ?? "");
    setReady(true);
  }, [draft.data, ready]);

  const savedTitle = draft.data?.title ?? "";
  const savedBody = draft.data?.body ?? "";
  const changed = ready && (title !== savedTitle || body !== savedBody);
  const words = useMemo(() => wordCount(body), [body]);

  useEffect(() => {
    if (!changed || lock.isPending) return;
    const timer = window.setTimeout(() => {
      save.mutate({ title, body, word_count: words, reading_time_minutes: Math.max(1, Math.ceil(words / 220)) });
    }, 700);
    return () => window.clearTimeout(timer);
  }, [body, changed, lock.isPending, save, title, words]);

  if (!draftId) return <Navigate to="/dashboard" replace />;
  if (draft.isLoading || !ready) return <WorkspaceFrame><p className="text-muted-foreground">Loading your workspace…</p></WorkspaceFrame>;
  if (draft.isError || !draft.data) return <WorkspaceFrame><Card><CardContent className="p-6">This draft is unavailable. Return to your <Link className="text-primary underline" to="/dashboard">dashboard</Link>.</CardContent></Card></WorkspaceFrame>;
  if (draft.data.locked_at) return <Navigate to={`/drafts/${draftId}/setup`} replace />;

  async function handleLock() {
    await lock.mutateAsync({ title, body, word_count: words, reading_time_minutes: Math.max(1, Math.ceil(words / 220)) });
    navigate(`/drafts/${draftId}/setup`, { replace: true });
  }

  return (
    <WorkspaceFrame>
      <div className="mb-10 flex items-center justify-between border-b border-border/70 pb-5">
        <div>
          <Link to="/dashboard" className="text-sm text-muted-foreground hover:text-foreground">← Library</Link>
          <p className="mt-4 text-xs font-semibold uppercase tracking-[0.18em] text-primary">First draft</p>
          <h1 className="mt-1 font-serif text-3xl tracking-tight text-foreground">Make your case.</h1>
        </div>
        <div className="flex items-center gap-3 text-sm text-muted-foreground">
          <Save className="h-4 w-4" />
          {save.isPending ? "Saving…" : changed ? "Saving changes…" : "Saved"}
        </div>
      </div>

      <div className="mx-auto max-w-3xl">
        <Card className="writing-canvas border-[#d9d0c2] bg-[#fbfaf6]">
          <CardHeader className="px-8 pb-2 pt-10 md:px-14">
            <CardDescription className="text-xs uppercase tracking-[0.18em]">Write without interruption</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6 px-8 pb-12 md:px-14">
            <div className="space-y-2">
              <Input id="draft-title" value={title} onChange={(event) => setTitle(event.target.value)} className="typewriter-title h-auto border-0 border-b border-[#d9d0c2] bg-transparent px-0 py-3 text-2xl font-bold shadow-none focus-visible:ring-0" placeholder="Untitled" />
            </div>
            <div className="space-y-2">
              <Textarea id="draft-body" value={body} onChange={(event) => setBody(event.target.value)} className="typewriter-body min-h-[31rem] resize-none border-0 bg-transparent px-0 text-[1.05rem] shadow-none focus-visible:ring-0" placeholder="Begin with what you believe, notice, or need to decide…" />
              <p className="text-right text-xs text-muted-foreground">{words} words · about {Math.max(1, Math.ceil(words / 220))} min read</p>
            </div>
          </CardContent>
        </Card>
        <div className="mt-6 flex flex-col items-center justify-between gap-4 sm:flex-row"><p className="text-sm text-muted-foreground">Your original draft stays private until you choose to preserve it.</p><Button size="lg" disabled={!body.trim() || lock.isPending} onClick={() => setShowLock(true)}><LockKeyhole className="mr-2 h-4 w-4" />{lock.isPending ? "Preserving…" : "Preserve this draft"}</Button></div>
        {!body.trim() ? <p className="mt-3 text-center text-xs text-muted-foreground">Start with a thought. AI comes later.</p> : null}
      </div>

      {showLock ? <div className="fixed inset-0 z-50 grid place-items-center bg-foreground/35 p-4"><Card className="w-full max-w-lg shadow-xl"><CardHeader><Badge variant="human" className="w-fit">Irreversible step</Badge><CardTitle>Preserve this baseline?</CardTitle><CardDescription>You can no longer edit this original version after locking. You will be able to invite AI to challenge it and review every accepted addition.</CardDescription></CardHeader><CardContent className="flex justify-end gap-3"><Button variant="outline" onClick={() => setShowLock(false)}>Keep writing</Button><Button onClick={() => void handleLock()}>Lock and invite AI <ArrowRight className="ml-2 h-4 w-4" /></Button></CardContent></Card></div> : null}
    </WorkspaceFrame>
  );
}

function WorkspaceFrame({ children }: { children: ReactNode }) {
  return <main className="min-h-screen bg-background px-5 py-8 text-foreground md:px-10"><div className="mx-auto max-w-4xl">{children}</div></main>;
}
