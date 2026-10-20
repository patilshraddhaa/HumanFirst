import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link, Navigate, useNavigate, useParams } from "react-router-dom";
import { ArrowRight, Check, LockKeyhole, Save, Sparkles } from "lucide-react";

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
      <div className="mb-8 flex flex-col gap-5 border-b border-border pb-7 md:flex-row md:items-end md:justify-between">
        <div>
          <Link to="/dashboard" className="text-sm font-medium text-muted-foreground hover:text-foreground">← All work</Link>
          <p className="mt-6 text-xs font-semibold uppercase tracking-[0.18em] text-primary">Step 1 · Form your position</p>
          <h1 className="mt-2 font-serif text-4xl tracking-tight text-foreground md:text-5xl">Think first. Then invite challenge.</h1>
          <p className="mt-3 max-w-2xl text-base leading-7 text-muted-foreground">Write the claim, question, or argument in your own words. This becomes the human baseline that stays visible.</p>
        </div>
        <div className="flex items-center gap-3 text-sm text-muted-foreground">
          <Save className="h-4 w-4" />
          {save.isPending ? "Saving…" : changed ? "Saving changes…" : "Saved"}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <Card>
          <CardHeader>
            <CardTitle>Human baseline</CardTitle>
            <CardDescription>Your original thinking is preserved before AI enters the process.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="space-y-2">
              <label htmlFor="draft-title" className="text-sm font-medium">Working title</label>
              <Input id="draft-title" value={title} onChange={(event) => setTitle(event.target.value)} placeholder="What are you trying to understand or argue?" />
            </div>
            <div className="space-y-2">
              <label htmlFor="draft-body" className="text-sm font-medium">Your thinking</label>
              <Textarea id="draft-body" value={body} onChange={(event) => setBody(event.target.value)} className="min-h-[28rem] resize-y text-base leading-7" placeholder="Start with what you believe, notice, or need to decide…" />
              <p className="text-right text-xs text-muted-foreground">{words} words · about {Math.max(1, Math.ceil(words / 220))} min read</p>
            </div>
          </CardContent>
        </Card>

        <aside className="space-y-4">
          <Card className="border-primary/20 bg-secondary/40">
            <CardHeader className="pb-3"><Badge variant="human" className="w-fit">Human first</Badge><CardTitle className="text-xl">Your point of view comes first.</CardTitle></CardHeader>
            <CardContent className="text-sm leading-6 text-muted-foreground">AI should make your thinking stronger—not arrive early enough to replace it.</CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3"><CardTitle className="text-lg">What happens next</CardTitle></CardHeader>
            <CardContent className="space-y-4 text-sm">
              <FlowStep icon={<LockKeyhole />} title="Preserve the baseline" body="Lock this version when it represents your starting position." />
              <FlowStep icon={<Sparkles />} title="Invite AI deliberately" body="Ask for challenge, evidence, viewpoints, or structure—not a replacement draft." />
              <FlowStep icon={<Check />} title="Make revision legible" body="Review what changed and choose what to accept before publishing." />
            </CardContent>
          </Card>
          <Button className="w-full" size="lg" disabled={!body.trim() || lock.isPending} onClick={() => setShowLock(true)}><LockKeyhole className="mr-2 h-4 w-4" />{lock.isPending ? "Preserving baseline…" : "Preserve human baseline"}</Button>
          {!body.trim() ? <p className="text-center text-xs text-muted-foreground">Write a first thought to continue.</p> : null}
        </aside>
      </div>

      {showLock ? <div className="fixed inset-0 z-50 grid place-items-center bg-foreground/35 p-4"><Card className="w-full max-w-lg shadow-xl"><CardHeader><Badge variant="human" className="w-fit">Irreversible step</Badge><CardTitle>Preserve this baseline?</CardTitle><CardDescription>You can no longer edit this original version after locking. You will be able to invite AI to challenge it and review every accepted addition.</CardDescription></CardHeader><CardContent className="flex justify-end gap-3"><Button variant="outline" onClick={() => setShowLock(false)}>Keep writing</Button><Button onClick={() => void handleLock()}>Lock and invite AI <ArrowRight className="ml-2 h-4 w-4" /></Button></CardContent></Card></div> : null}
    </WorkspaceFrame>
  );
}

function FlowStep({ icon, title, body }: { icon: ReactNode; title: string; body: string }) {
  return <div className="flex gap-3"><span className="mt-0.5 text-primary">{icon}</span><div><p className="font-medium">{title}</p><p className="mt-1 leading-5 text-muted-foreground">{body}</p></div></div>;
}

function WorkspaceFrame({ children }: { children: ReactNode }) {
  return <main className="min-h-screen bg-background px-5 py-8 text-foreground md:px-10"><div className="mx-auto max-w-6xl">{children}</div></main>;
}
