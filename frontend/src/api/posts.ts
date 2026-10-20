import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createPostComment,
  getPostBySlug,
  likePost,
  listPosts,
  unlikePost,
} from "../client/sdk.gen";
import type {
  PostCommentCreateRequest,
  PostCommentThreadResponse,
  PostListResponse,
  PostProvenanceResponse,
  PostSectionResponse,
  PublicPostDetailResponse,
} from "../client/types.gen";

export type { PostSectionResponse, PostCommentThreadResponse, PostProvenanceResponse };

// Re-export the canonical post type so consumers import from one place.
export type { PublicPostDetailResponse as PublicPostResponse };

export function useListPosts() {
  return useQuery<PostListResponse>({
    queryKey: ["posts"],
    queryFn: async () => {
      const res = await listPosts();
      return res.data;
    },
  });
}

export function usePublicPost(slug: string) {
  return useQuery<PublicPostDetailResponse>({
    queryKey: ["public-post", slug],
    queryFn: async () => {
      const res = await getPostBySlug({ path: { slug } });
      return res.data;
    },
    enabled: slug.length > 0,
  });
}

// Fingerprint is derived from a stable browser identifier.
function getFingerprint(): string {
  const stored = sessionStorage.getItem("hf_fp");
  if (stored) return stored;
  const fp = `${navigator.userAgent}-${screen.width}x${screen.height}-${Date.now()}`;
  sessionStorage.setItem("hf_fp", fp);
  return fp;
}

export function useLikePublicPost(postId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () =>
      likePost({ path: { post_id: postId }, body: { fingerprint: getFingerprint() } }),
    onSuccess: ({ data }) => {
      queryClient.setQueryData<PublicPostDetailResponse | undefined>(
        ["public-post-by-id", postId],
        (current) => current ? { ...current, like_count: data.like_count } : current,
      );
    },
  });
}

export function useUnlikePublicPost(postId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () =>
      unlikePost({ path: { post_id: postId }, body: { fingerprint: getFingerprint() } }),
    onSuccess: ({ data }) => {
      queryClient.setQueryData<PublicPostDetailResponse | undefined>(
        ["public-post-by-id", postId],
        (current) => current ? { ...current, like_count: data.like_count } : current,
      );
    },
  });
}

export function useCreatePublicComment(postId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: PostCommentCreateRequest) =>
      createPostComment({ path: { post_id: postId }, body: payload }),
    onSuccess: ({ data: envelope }) => {
      queryClient.setQueryData<PublicPostDetailResponse | undefined>(
        ["public-post-by-id", postId],
        (current) => {
          if (!current) return current;
          const newComment: PostCommentThreadResponse = { ...envelope.comment, replies: [] };
          return { ...current, comments: [...current.comments, newComment], comment_count: envelope.comment_count };
        },
      );
    },
  });
}
