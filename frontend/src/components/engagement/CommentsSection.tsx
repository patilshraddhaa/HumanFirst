import type { PostCommentThreadResponse } from "../../client/types.gen";
import { ActionButton } from "../shared";

type CommentsSectionProps = {
  comments: PostCommentThreadResponse[];
  errorMessage: string | null;
  isSubmitting: boolean;
  authorName: string;
  authorEmail: string;
  onAuthorNameChange: (value: string) => void;
  onAuthorEmailChange: (value: string) => void;
  onCommentBodyChange: (value: string) => void;
  onSubmit: () => void;
  value: string;
};

export function CommentsSection({
  comments,
  errorMessage,
  isSubmitting,
  authorName,
  authorEmail,
  onAuthorNameChange,
  onAuthorEmailChange,
  onCommentBodyChange,
  onSubmit,
  value,
}: CommentsSectionProps) {
  const canSubmit = value.trim().length > 0 && authorName.trim().length > 0 && authorEmail.trim().length > 0;

  return (
    <section className="rounded-[2rem] border border-white/70 bg-white/90 p-8 shadow-[0_24px_80px_rgba(52,58,64,0.08)]">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500">
            Comments
          </p>
          <h2 className="mt-3 font-['Fraunces'] text-3xl text-stone-900">
            Reader discussion
          </h2>
        </div>
        <p className="text-sm text-stone-500">{comments.length} total</p>
      </div>

      <div className="mt-6 grid gap-3">
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="block">
            <span className="text-sm font-medium text-stone-700">Name</span>
            <input
              value={authorName}
              onChange={(e) => onAuthorNameChange(e.target.value)}
              className="mt-2 w-full rounded-[1rem] border border-stone-200 bg-stone-50 px-4 py-3 text-base text-stone-900 outline-none transition focus:border-emerald-500"
              placeholder="Your name"
            />
          </label>
          <label className="block">
            <span className="text-sm font-medium text-stone-700">Email</span>
            <input
              type="email"
              value={authorEmail}
              onChange={(e) => onAuthorEmailChange(e.target.value)}
              className="mt-2 w-full rounded-[1rem] border border-stone-200 bg-stone-50 px-4 py-3 text-base text-stone-900 outline-none transition focus:border-emerald-500"
              placeholder="you@example.com"
            />
          </label>
        </div>
        <label className="block">
          <span className="text-sm font-medium text-stone-700">Comment</span>
          <textarea
            value={value}
            onChange={(event) => onCommentBodyChange(event.target.value)}
            className="mt-2 min-h-[8rem] w-full rounded-[1.5rem] border border-stone-200 bg-stone-50 px-5 py-4 text-base leading-7 text-stone-900 outline-none transition focus:border-emerald-500"
            placeholder="What should the author clarify or expand?"
          />
        </label>
      </div>

      <div className="mt-4 flex items-center justify-between gap-4">
        <p className="text-sm text-stone-500">
          Comments post directly to the public engagement API.
        </p>
        <ActionButton onClick={onSubmit} disabled={isSubmitting || !canSubmit}>
          {isSubmitting ? "Posting..." : "Post comment"}
        </ActionButton>
      </div>

      {errorMessage ? (
        <p className="mt-4 text-sm font-semibold text-rose-700">{errorMessage}</p>
      ) : null}

      <div className="mt-8 grid gap-4">
        {comments.map((comment) => (
          <article
            key={comment.id}
            className="rounded-[1.5rem] border border-stone-200 bg-[#fffcf6] p-5"
          >
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="font-semibold text-stone-900">{comment.author_name}</p>
              <p className="text-sm text-stone-500">
                {new Date(comment.created_at).toLocaleString("en-US", {
                  month: "short",
                  day: "numeric",
                  hour: "numeric",
                  minute: "2-digit",
                })}
              </p>
            </div>
            <p className="mt-3 whitespace-pre-wrap text-base leading-7 text-stone-700">
              {comment.body}
            </p>
            {comment.replies.length > 0 ? (
              <div className="mt-4 grid gap-3 pl-5 border-l-2 border-stone-200">
                {comment.replies.map((reply) => (
                  <div key={reply.id} className="rounded-[1rem] border border-stone-100 bg-stone-50 p-4">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm font-semibold text-stone-800">{reply.author_name}</p>
                      <p className="text-xs text-stone-400">
                        {new Date(reply.created_at).toLocaleString("en-US", { month: "short", day: "numeric" })}
                      </p>
                    </div>
                    <p className="mt-2 text-sm leading-6 text-stone-600">{reply.body}</p>
                  </div>
                ))}
              </div>
            ) : null}
          </article>
        ))}
        {comments.length === 0 ? (
          <div className="rounded-[1.5rem] border border-dashed border-stone-300 bg-stone-50 px-5 py-6 text-sm text-stone-500">
            No comments yet. Start the review loop from the public page.
          </div>
        ) : null}
      </div>
    </section>
  );
}
