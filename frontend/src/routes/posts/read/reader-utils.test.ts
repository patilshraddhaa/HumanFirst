import { describe, expect, it } from "vitest";
import type { PostSectionResponse, PublicPostDetailResponse } from "../../../client/types.gen";
import {
  buildReaderSearchParams,
  getAuthenticityWordCounts,
  getAuthorInitials,
  getRenderableSections,
  getReaderViewMode,
} from "./reader-utils";

function makeSection(overrides: Partial<PostSectionResponse> & { id: string }): PostSectionResponse {
  return {
    ordinal: 1,
    author_type: "HUMAN",
    content_type: "BODY_PARAGRAPH",
    content: "body",
    anchor_human_section_id: null,
    word_count: 1,
    ...overrides,
  };
}

function makePost(overrides: Partial<PublicPostDetailResponse>): PublicPostDetailResponse {
  return {
    id: "post-1",
    author_id: "author-1",
    author_display_name: null,
    slug: "story",
    title: "Story",
    like_count: 0,
    comment_count: 0,
    human_word_count: 88,
    ai_word_count: 12,
    provenance: {
      total_sections: 2,
      human_sections: 1,
      ai_sections: 1,
      human_word_count: 88,
      ai_word_count: 12,
      total_word_count: 100,
      has_ai_content: true,
      by_author_type: [],
      by_content_type: [],
    },
    published_at: "2026-05-28T00:00:00.000Z",
    updated_at: "2026-05-28T00:00:00.000Z",
    sections: [],
    comments: [],
    ...overrides,
  };
}

describe("reader-utils", () => {
  it("reads human mode from the query string", () => {
    expect(getReaderViewMode(new URLSearchParams("view=human"))).toBe("human");
    expect(getReaderViewMode(new URLSearchParams(""))).toBe("default");
  });

  it("adds and removes the human mode query parameter", () => {
    expect(buildReaderSearchParams(new URLSearchParams("foo=bar"), "human").toString()).toBe(
      "foo=bar&view=human",
    );
    expect(
      buildReaderSearchParams(new URLSearchParams("foo=bar&view=human"), "default").toString(),
    ).toBe("foo=bar");
  });

  it("filters AI sections in human mode and preserves ordinal order", () => {
    const sections: PostSectionResponse[] = [
      makeSection({ id: "two", ordinal: 2, author_type: "AI", content: "AI body" }),
      makeSection({ id: "three", ordinal: 3, author_type: "AI", content: "Machine only" }),
      makeSection({ id: "one", ordinal: 1, author_type: "HUMAN", content: "Human body" }),
    ];

    const result = getRenderableSections(sections, "human");
    expect(result).toHaveLength(1);
    expect(result[0]).toMatchObject({ id: "one", displayBody: "Human body" });
  });

  it("returns all sections in default mode", () => {
    const sections: PostSectionResponse[] = [
      makeSection({ id: "h1", ordinal: 1, author_type: "HUMAN", content: "Human" }),
      makeSection({ id: "a1", ordinal: 2, author_type: "AI", content: "AI" }),
    ];

    expect(getRenderableSections(sections, "default")).toHaveLength(2);
  });

  it("reads authenticity word counts from post", () => {
    expect(getAuthenticityWordCounts(makePost({}))).toEqual({ aiWords: 12, humanWords: 88 });
  });

  it("builds initials from the first two name parts", () => {
    expect(getAuthorInitials("Ada Lovelace")).toBe("AL");
    expect(getAuthorInitials("Single")).toBe("S");
  });
});
