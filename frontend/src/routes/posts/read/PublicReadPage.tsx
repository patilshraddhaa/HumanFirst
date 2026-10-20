import { useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import {
  useCreatePublicComment,
  useLikePublicPost,
  usePublicPost,
  useUnlikePublicPost,
} from "../../../api/posts";
import { getErrorMessage } from "../../../api/errors";
import { CommentsSection } from "../../../components/engagement/CommentsSection";
import { EngagementRow } from "../../../components/engagement/EngagementRow";
import { ReadSection } from "../../../components/sections/ReadSection";
import {
  ActionButton,
  AuthenticityBar,
  ErrorState,
  LoadingState,
  PageShell,
  SectionStack,
} from "../../../components/shared";
import {
  buildReaderSearchParams,
  formatPublishedDate,
  getAuthenticityWordCounts,
  getAuthorInitials,
  getAuthorName,
  getReadTimeLabel,
  getReaderViewMode,
  getRenderableSections,
  type ReaderViewMode,
} from "./reader-utils";

export function PublicReadPage() {
  const { slug = "" } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const [commentBody, setCommentBody] = useState("");
  const [commentAuthorName, setCommentAuthorName] = useState("");
  const [commentAuthorEmail, setCommentAuthorEmail] = useState("");
  const [isLiked, setIsLiked] = useState(false);
  const [shareMessage, setShareMessage] = useState<string | null>(null);
  const viewMode = getReaderViewMode(searchParams);

  const postQuery = usePublicPost(slug);
  const post = postQuery.data;

  // Likes and comments use the post UUID (not the slug)
  const postId = post?.id ?? "";
  const likePost = useLikePublicPost(postId);
  const unlikePost = useUnlikePublicPost(postId);
  const createComment = useCreatePublicComment(postId);

  const sections = post ? getRenderableSections(post.sections, viewMode) : [];
  const authorName = post ? getAuthorName(post) : "";
  const authorInitials = getAuthorInitials(authorName);
  const baseAuthenticity = post ? getAuthenticityWordCounts(post) : { humanWords: 0, aiWords: 0 };
  const authenticity = {
    humanWords: baseAuthenticity.humanWords,
    aiWords: viewMode === "human" ? 0 : baseAuthenticity.aiWords,
  };

  function handleViewChange(nextView: ReaderViewMode) {
    setSearchParams(buildReaderSearchParams(searchParams, nextView), { replace: true });
  }

  async function handleShare() {
    const shareUrl = window.location.href;
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(shareUrl);
        setShareMessage("Link copied.");
      } else {
        setShareMessage("Share the URL from your browser.");
      }
    } catch {
      setShareMessage("Copy the URL from your browser.");
    }
  }

  async function handleLikeToggle() {
    if (!post) return;
    if (isLiked) {
      await unlikePost.mutateAsync();
      setIsLiked(false);
    } else {
      await likePost.mutateAsync();
      setIsLiked(true);
    }
  }

  async function handleCommentSubmit() {
    const body = commentBody.trim();
    const name = commentAuthorName.trim();
    const email = commentAuthorEmail.trim();
    if (!body || !name || !email) return;

    await createComment.mutateAsync({ body, author_name: name, author_email: email });
    setCommentBody("");
  }

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,_#f8f1e8_0%,_#f4f6f1_38%,_#eef3f8_100%)]">
      <PageShell
        eyebrow="Public reader"
        title={post?.title ?? "Loading story"}
        subtitle="Read the published version, inspect the human-only rendering, and engage without signing in."
        actions={
          <div className="inline-flex rounded-full border border-stone-300 bg-white/80 p-1 shadow-sm">
            <button
              type="button"
              onClick={() => handleViewChange("default")}
              className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                viewMode === "default" ? "bg-stone-900 text-white" : "text-stone-600"
              }`}
            >
              Full story
            </button>
            <button
              type="button"
              onClick={() => handleViewChange("human")}
              className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                viewMode === "human" ? "bg-stone-900 text-white" : "text-stone-600"
              }`}
            >
              Human only
            </button>
          </div>
        }
      >
        {postQuery.isLoading ? (
          <LoadingState
            title="Loading public story..."
            body="Pulling the published sections, authenticity data, and discussion."
          />
        ) : postQuery.isError || !post ? (
          <ErrorState
            title="Story unavailable"
            body="The public read view could not be loaded. Retry once the backend is reachable."
            actionLabel="Retry"
            onAction={() => void postQuery.refetch()}
          />
        ) : (
          <div className="grid gap-6 lg:grid-cols-[minmax(0,1.2fr)_20rem]">
            <SectionStack>
              <section className="rounded-[2rem] border border-white/70 bg-white/90 p-8 shadow-[0_24px_80px_rgba(52,58,64,0.1)]">
                <div className="flex flex-wrap items-center gap-4">
                  <div className="flex h-14 w-14 items-center justify-center rounded-full bg-stone-900 text-base font-semibold text-white">
                    {authorInitials}
                  </div>
                  <div className="min-w-0">
                    <p className="text-base font-semibold text-stone-900">{authorName}</p>
                    <p className="mt-1 text-sm text-stone-500">
                      {formatPublishedDate(post.published_at)} | {getReadTimeLabel(post, sections)}
                    </p>
                  </div>
                </div>
                <div className="mt-7">
                  <AuthenticityBar aiWords={authenticity.aiWords} humanWords={authenticity.humanWords} />
                </div>
              </section>

              {sections.map((section, index) => (
                <div
                  key={section.id}
                  className="transition-all duration-200 ease-in-out"
                  style={{ animation: "fadeIn 200ms ease-in-out" }}
                >
                  <ReadSection
                    body={section.displayBody}
                    index={index + 1}
                    title={`${section.author_type === "HUMAN" ? "Human" : "AI"} · ${section.content_type.replace(/_/g, " ")}`}
                    tone={viewMode === "human" ? "human" : section.author_type === "HUMAN" ? "human" : "ai"}
                  />
                </div>
              ))}

              <footer className="rounded-[2rem] border border-stone-200 bg-[#fffaf2] p-8 shadow-[0_20px_60px_rgba(15,23,42,0.05)]">
                <p className="text-xs font-semibold uppercase tracking-[0.28em] text-stone-500">
                  Provenance
                </p>
                <p className="mt-3 font-['Fraunces'] text-3xl text-stone-900">
                  Verification trail for this published view
                </p>
                <div className="mt-4 grid gap-2 text-sm text-stone-600">
                  <p>Human words: {post.human_word_count} · AI words: {post.ai_word_count}</p>
                  <p>Sections: {post.provenance.human_sections} human, {post.provenance.ai_sections} AI</p>
                </div>
              </footer>

              <CommentsSection
                comments={post.comments}
                errorMessage={
                  createComment.isError
                    ? getErrorMessage(createComment.error, "Comment submission failed.")
                    : null
                }
                isSubmitting={createComment.isPending}
                authorName={commentAuthorName}
                authorEmail={commentAuthorEmail}
                onAuthorNameChange={setCommentAuthorName}
                onAuthorEmailChange={setCommentAuthorEmail}
                onCommentBodyChange={setCommentBody}
                onSubmit={() => void handleCommentSubmit()}
                value={commentBody}
              />
            </SectionStack>

            <aside className="grid content-start gap-5">
              <EngagementRow
                commentCount={post.comment_count}
                isLiking={likePost.isPending || unlikePost.isPending}
                isSharing={false}
                liked={isLiked}
                likeCount={post.like_count}
                onLikeToggle={() => void handleLikeToggle()}
                onShare={() => void handleShare()}
                shareCount={0}
              />

              <div className="rounded-[2rem] border border-white/70 bg-white/85 p-6 shadow-[0_18px_60px_rgba(15,23,42,0.06)]">
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500">
                  View mode
                </p>
                <p className="mt-3 text-sm leading-6 text-stone-600">
                  {viewMode === "human"
                    ? "Human only mode is active — AI sections are hidden."
                    : "Full story mode shows both human and AI-assisted content."}
                </p>
                {shareMessage ? (
                  <p className="mt-4 text-sm font-semibold text-emerald-700">{shareMessage}</p>
                ) : null}
              </div>

              <div className="rounded-[2rem] border border-stone-200 bg-stone-900 p-6 text-stone-100 shadow-[0_20px_60px_rgba(15,23,42,0.12)]">
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-400">
                  Reader surface
                </p>
                <p className="mt-3 font-['Fraunces'] text-3xl">
                  Public, shareable, and traceable.
                </p>
                <p className="mt-3 text-sm leading-6 text-stone-300">
                  Likes and comments call backend APIs so engagement remains attached to the published artifact.
                </p>
                <div className="mt-5">
                  <ActionButton
                    variant="secondary"
                    className="w-full border-white/20 bg-white/10 text-white hover:bg-white/15"
                    onClick={() => void handleShare()}
                  >
                    Share this story
                  </ActionButton>
                </div>
              </div>
            </aside>
          </div>
        )}
      </PageShell>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(-8px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
