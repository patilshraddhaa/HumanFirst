import { ArrowRight, Check, Eye, LockKeyhole } from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { useDraft, useUpdateDraft } from "../../../api/drafts";
import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../components/ui/card";

export function DraftPreviewPage() {
  const { draftId = "" } = useParams();
  const draft = useDraft(draftId);
  const publish = useUpdateDraft(draftId);
  const data = draft.data;

  return <main className="min-h-screen bg-background px-5 py-8 text-foreground md:px-10"><div className="mx-auto max-w-5xl">
    <Link to="/dashboard" className="text-sm font-medium text-muted-foreground hover:text-foreground">← All work</Link>
    <div className="mt-8 flex flex-col gap-5 border-b border-border pb-7 md:flex-row md:items-end md:justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">Step 3 · Make revision legible</p><h1 className="mt-2 font-serif text-4xl tracking-tight md:text-5xl">Review what is yours.</h1><p className="mt-3 max-w-2xl leading-7 text-muted-foreground">Your human baseline remains visible. Any AI-assisted additions are clearly marked before you publish.</p></div><Button size="lg" disabled={!data?.locked_at || publish.isPending} onClick={() => void publish.mutateAsync({ status: "published" })}>{publish.isPending ? "Publishing…" : "Publish with provenance"}<ArrowRight className="ml-2 h-4 w-4" /></Button></div>
    {draft.isLoading ? <p className="mt-10 text-muted-foreground">Loading review…</p> : null}
    {draft.isError || !data ? <Card className="mt-8"><CardContent className="p-6">This draft could not be loaded.</CardContent></Card> : null}
    {data ? <div className="mt-8 grid gap-6 lg:grid-cols-[minmax(0,1fr)_18rem]"><div className="space-y-6"><Card><CardHeader><Badge variant="human" className="w-fit">Human baseline</Badge><CardTitle>{data.title || "Untitled draft"}</CardTitle><CardDescription>{data.word_count} words written before AI entered the process.</CardDescription></CardHeader><CardContent className="whitespace-pre-wrap text-base leading-8 text-foreground/85">{data.body}</CardContent></Card></div><aside className="space-y-4"><Card><CardHeader><Eye className="h-5 w-5 text-primary"/><CardTitle className="text-xl">Provenance summary</CardTitle></CardHeader><CardContent className="space-y-3 text-sm"><div className="flex justify-between"><span className="text-muted-foreground">Human-written</span><span className="font-medium">{data.word_count} words</span></div><div className="flex justify-between"><span className="text-muted-foreground">AI-assisted</span><span className="font-medium">0 words</span></div><p className="border-t border-border pt-3 leading-5 text-muted-foreground">AI-assisted sections added through MCP will appear here with their source and placement.</p></CardContent></Card><Card className="border-primary/20 bg-secondary/40"><CardHeader><LockKeyhole className="h-5 w-5 text-primary"/><CardTitle className="text-lg">Baseline protected</CardTitle></CardHeader><CardContent className="text-sm leading-6 text-muted-foreground">This original version is locked. Publishing preserves the distinction between your work and AI contributions.</CardContent></Card></aside></div> : null}
    {publish.isError ? <p className="mt-5 text-sm text-destructive">Publishing failed. Please try again.</p> : null}
    {publish.isSuccess ? <p className="mt-5 flex items-center gap-2 text-sm text-primary"><Check className="h-4 w-4" />Published locally. Your baseline and provenance are saved in this browser.</p> : null}
  </div></main>;
}
