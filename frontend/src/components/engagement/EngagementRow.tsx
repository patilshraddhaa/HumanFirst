import { ActionButton } from "../shared";

type EngagementRowProps = {
  commentCount: number;
  isLiking: boolean;
  isSharing: boolean;
  liked: boolean;
  likeCount: number;
  onLikeToggle: () => void;
  onShare: () => void;
  shareCount: number;
};

export function EngagementRow({
  commentCount,
  isLiking,
  isSharing,
  liked,
  likeCount,
  onLikeToggle,
  onShare,
  shareCount,
}: EngagementRowProps) {
  return (
    <div className="rounded-[2rem] border border-white/70 bg-white/85 p-6 shadow-[0_18px_60px_rgba(15,23,42,0.06)]">
      <p className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500">
        Engagement
      </p>
      <div className="mt-5 grid gap-3">
        <div className="grid grid-cols-3 gap-3 text-center">
          <MetricCard label="Likes" value={likeCount} />
          <MetricCard label="Comments" value={commentCount} />
          <MetricCard label="Shares" value={shareCount} />
        </div>
        <ActionButton onClick={onLikeToggle} disabled={isLiking}>
          {isLiking ? "Saving..." : liked ? "Unlike" : "Like"}
        </ActionButton>
        <ActionButton variant="secondary" onClick={onShare} disabled={isSharing}>
          {isSharing ? "Sharing..." : "Share"}
        </ActionButton>
      </div>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-[1.25rem] border border-stone-200 bg-stone-50 px-3 py-4">
      <p className="text-lg font-semibold text-stone-900">{value}</p>
      <p className="mt-1 text-xs font-medium uppercase tracking-[0.18em] text-stone-500">
        {label}
      </p>
    </div>
  );
}
