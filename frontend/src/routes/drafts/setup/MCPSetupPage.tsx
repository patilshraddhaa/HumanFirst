import { useEffect, useMemo, useState } from "react";
import { ArrowRight, Check, MessageSquareText, Scale, Search, ShieldCheck, X } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

import { useDraft } from "../../../api/drafts";
import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../components/ui/card";
import { Textarea } from "../../../components/ui/textarea";

type ChallengeMode = "assumptions" | "opposing-case" | "evidence" | "structure";
type Decision = "defend" | "revise" | "evidence" | "dismiss";
type Reflection = { mode: ChallengeMode; response: string; decision: Decision | null };

const challengeModes: Array<{ id: ChallengeMode; label: string; description: string }> = [
  { id: "assumptions", label: "Challenge assumptions", description: "Test what your argument takes for granted." },
  { id: "opposing-case", label: "Make the opposing case", description: "Consider the strongest reasonable disagreement." },
  { id: "evidence", label: "Find missing evidence", description: "Spot claims that need proof, examples, or limits." },
  { id: "structure", label: "Improve structure", description: "Check whether a skeptical reader can follow your logic." },
];

const prompts: Record<ChallengeMode, string> = {
  assumptions: "What assumption must be true for this claim to hold? Who or what might challenge it?",
  "opposing-case": "What is the strongest reasonable case against this claim?",
  evidence: "Which part of this claim needs evidence, an example, or a clearer boundary?",
  structure: "What would a skeptical reader need to understand before they can accept this claim?",
};

const decisions: Array<{ id: Decision; label: string; icon: typeof ShieldCheck }> = [
  { id: "defend", label: "Defend", icon: ShieldCheck },
  { id: "revise", label: "Revise", icon: MessageSquareText },
  { id: "evidence", label: "Ask for evidence", icon: Search },
  { id: "dismiss", label: "Dismiss", icon: X },
];

function reflectionKey(draftId: string) {
  return `humanfirst-reflection-${draftId}`;
}

export function MCPSetupPage() {
  const { draftId = "" } = useParams();
  const navigate = useNavigate();
  const draft = useDraft(draftId);
  const [mode, setMode] = useState<ChallengeMode>("assumptions");
  const [response, setResponse] = useState("");
  const [decision, setDecision] = useState<Decision | null>(null);

  const claim = useMemo(() => {
    const firstParagraph = draft.data?.body.trim().split(/\n+/).find(Boolean);
    return firstParagraph || "State your central claim.";
  }, [draft.data?.body]);

  useEffect(() => {
    const saved = localStorage.getItem(reflectionKey(draftId));
    if (!saved) return;
    try {
      const reflection = JSON.parse(saved) as Reflection;
      setMode(reflection.mode);
      setResponse(reflection.response);
      setDecision(reflection.decision);
    } catch {
      localStorage.removeItem(reflectionKey(draftId));
    }
  }, [draftId]);

  function saveDecision(nextDecision: Decision) {
    setDecision(nextDecision);
    localStorage.setItem(reflectionKey(draftId), JSON.stringify({ mode, response, decision: nextDecision }));
  }

  function continueToReview() {
    localStorage.setItem(reflectionKey(draftId), JSON.stringify({ mode, response, decision }));
    navigate(`/drafts/${draftId}/preview`);
  }

  return <main className="min-h-screen bg-background px-5 py-8 text-foreground md:px-10">
    <div className="mx-auto max-w-5xl">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">Step 2 · Stress-test your thinking</p>
      <h1 className="mt-2 max-w-3xl font-serif text-4xl tracking-tight md:text-5xl">Let AI sharpen the argument—without taking it over.</h1>
      <p className="mt-3 max-w-2xl leading-7 text-muted-foreground">Choose one kind of productive pressure. Respond in your own words, then decide what belongs in the draft.</p>

      <div className="mt-8 grid gap-6 lg:grid-cols-[1fr_20rem]">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <Badge variant="human" className="w-fit">Your baseline</Badge>
              <CardTitle>{draft.data?.title || "Untitled draft"}</CardTitle>
              <CardDescription>{draft.data ? `${draft.data.word_count} human-written words are preserved and attributable.` : "Loading your baseline…"}</CardDescription>
            </CardHeader>
          </Card>

          <section aria-labelledby="challenge-type">
            <h2 id="challenge-type" className="mb-3 font-serif text-xl">Choose the challenge</h2>
            <div className="grid gap-3 sm:grid-cols-2">
              {challengeModes.map((option) => <button key={option.id} type="button" onClick={() => setMode(option.id)} className={`rounded-lg border p-4 text-left transition-colors ${mode === option.id ? "border-primary bg-primary/5 ring-1 ring-primary" : "border-border bg-card hover:bg-muted/50"}`}>
                <p className="font-medium">{option.label}</p>
                <p className="mt-1 text-sm leading-5 text-muted-foreground">{option.description}</p>
              </button>)}
            </div>
          </section>

          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <Badge variant="human" className="w-fit">Your claim</Badge>
                <CardDescription>From your locked baseline</CardDescription>
              </CardHeader>
              <CardContent><p className="font-serif text-lg leading-8">{claim}</p></CardContent>
            </Card>
            <Card className="border-primary/25 bg-secondary/30">
              <CardHeader>
                <Badge variant="ai" className="w-fit">Critical partner</Badge>
                <CardDescription>A focused question, not a rewrite</CardDescription>
              </CardHeader>
              <CardContent><p className="text-lg leading-8">{prompts[mode]}</p></CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-xl">Your response</CardTitle>
              <CardDescription>Write what you think before changing the draft. This note stays with your decision.</CardDescription>
            </CardHeader>
            <CardContent>
              <Textarea value={response} onChange={(event) => setResponse(event.target.value)} placeholder="What does this challenge make you reconsider, defend, or look into?" className="min-h-32 resize-y bg-background font-serif text-base leading-7" />
              <div className="mt-4 flex flex-wrap gap-2">
                {decisions.map(({ id, label, icon: Icon }) => <Button key={id} type="button" variant={decision === id ? "default" : "outline"} size="sm" onClick={() => saveDecision(id)}>
                  <Icon className="mr-2 h-3.5 w-3.5" />{label}
                </Button>)}
              </div>
              {decision && <p className="mt-3 flex items-center gap-2 text-sm text-muted-foreground"><Check className="h-4 w-4 text-primary" />Your choice is recorded. You remain the editor.</p>}
            </CardContent>
          </Card>
        </div>

        <aside className="space-y-4">
          <Card className="border-primary/20 bg-secondary/40">
            <CardHeader><Scale className="h-5 w-5 text-primary" /><CardTitle className="text-xl">Your call</CardTitle></CardHeader>
            <CardContent className="leading-6 text-muted-foreground">AI can challenge the work. It does not get to decide what you believe, write, or publish.</CardContent>
          </Card>
          <Button className="w-full" size="lg" disabled={!decision} onClick={continueToReview}>Continue to review <ArrowRight className="ml-2 h-4 w-4" /></Button>
          <p className="text-center text-xs leading-5 text-muted-foreground">Choose a response first. You can revisit this reflection before publishing.</p>
        </aside>
      </div>
    </div>
  </main>;
}
