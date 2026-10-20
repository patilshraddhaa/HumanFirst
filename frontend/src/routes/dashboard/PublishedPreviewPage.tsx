import { Link, useParams } from "react-router-dom";

export function PublishedPreviewPage() {
  const { slug } = useParams();

  return (
    <div className="min-h-screen bg-white-200 px-6 py-12 lg:px-12">
      <div className="mx-auto max-w-4xl rounded-[28px] border border-ml-grey-lightest bg-white p-8 shadow-[0_24px_80px_rgba(15,23,42,0.08)]">
        <Link className="text-sm font-medium text-ml-blue" to="/dashboard">
          ← Back to dashboard
        </Link>
        <p className="mt-8 text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">
          Published preview
        </p>
        <h1 className="mt-3 font-display text-[2.8rem] font-semibold tracking-[-0.05em] text-foreground">
          {slug}
        </h1>
        <p className="mt-4 max-w-2xl text-base leading-7 text-ml-grey-dark">
          This lightweight public route exists so published draft rows have a
          valid destination during the POC. The reader experience is owned by a
          later story.
        </p>
      </div>
    </div>
  );
}
