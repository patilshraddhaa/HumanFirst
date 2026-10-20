import type { PostSectionResponse, PublicPostDetailResponse } from "../../../client/types.gen";

export type ReaderViewMode = "default" | "human";

export type RenderableSection = PostSectionResponse & {
  displayBody: string;
};

export function getReaderViewMode(searchParams: URLSearchParams): ReaderViewMode {
  return searchParams.get("view") === "human" ? "human" : "default";
}

export function buildReaderSearchParams(
  searchParams: URLSearchParams,
  viewMode: ReaderViewMode,
) {
  const next = new URLSearchParams(searchParams);
  if (viewMode === "human") {
    next.set("view", "human");
  } else {
    next.delete("view");
  }
  return next;
}

export function getAuthorName(post: PublicPostDetailResponse) {
  return post.author_display_name ?? "Unknown author";
}

export function getAuthorInitials(name: string) {
  return (
    name
      .split(" ")
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase())
      .join("") || "?"
  );
}

export function getAuthenticityWordCounts(post: PublicPostDetailResponse) {
  return {
    humanWords: post.human_word_count,
    aiWords: post.ai_word_count,
  };
}

export function getRenderableSections(
  sections: PostSectionResponse[],
  viewMode: ReaderViewMode,
): RenderableSection[] {
  return [...sections]
    .sort((a, b) => a.ordinal - b.ordinal)
    .flatMap((section) => {
      const isHuman = section.author_type === "HUMAN";

      if (viewMode === "default") {
        return [{ ...section, displayBody: section.content }];
      }

      // human-only mode: keep human sections, drop AI sections
      if (isHuman) {
        return [{ ...section, displayBody: section.content }];
      }

      return [];
    });
}

export function formatPublishedDate(value: string) {
  return new Date(value).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function getReadTimeLabel(_post: PublicPostDetailResponse, visibleSections: RenderableSection[]) {
  const words = visibleSections.reduce(
    (sum, section) => sum + section.displayBody.trim().split(/\s+/).filter(Boolean).length,
    0,
  );
  const minutes = Math.max(1, Math.ceil(words / 200));
  return `${minutes} min read`;
}

export function getShareUrl(): string {
  return window.location.href;
}
