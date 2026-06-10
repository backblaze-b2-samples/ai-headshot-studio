"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ApiError,
  captionSubject,
  createSubject,
  deleteFile,
  generateHeadshots,
  getFiles,
  getFileStats,
  getPreviewUrl,
  getStudioStats,
  getStylePacks,
  getSubject,
  getSubjectGallery,
  getSubjectProgress,
  getSubjects,
  getUploadActivity,
  purgeSubject,
  trainSubject,
} from "@/lib/api-client";
import type { FileMetadata, SubjectStatus } from "@ai-headshot-studio/shared";

// Statuses where a background job is in flight — poll while in one of these.
const ACTIVE_STATUSES: SubjectStatus[] = ["captioning", "training", "generating"];

// Single source of truth for query keys. Keep these tightly scoped so that
// invalidating "files" doesn't blow away unrelated caches, and so an IDE
// "find usages" of `qk.files` reveals every consumer.
export const qk = {
  all: ["b2"] as const,
  files: (prefix?: string, limit?: number) =>
    [...qk.all, "files", prefix ?? "", limit ?? 100] as const,
  stats: () => [...qk.all, "stats"] as const,
  uploadActivity: (days: number) =>
    [...qk.all, "stats", "activity", days] as const,
  preview: (key: string) => [...qk.all, "preview", key] as const,
  studioStats: () => [...qk.all, "studio-stats"] as const,
  styles: () => [...qk.all, "styles"] as const,
  subjects: () => [...qk.all, "subjects"] as const,
  subject: (id: string) => [...qk.all, "subject", id] as const,
  subjectProgress: (id: string) => [...qk.all, "subject", id, "progress"] as const,
  subjectGallery: (id: string) => [...qk.all, "subject", id, "gallery"] as const,
};

export function useFiles(prefix = "", limit = 100) {
  return useQuery<FileMetadata[], ApiError>({
    queryKey: qk.files(prefix, limit),
    queryFn: () => getFiles(prefix, limit),
  });
}

export function useFileStats() {
  return useQuery({
    queryKey: qk.stats(),
    queryFn: getFileStats,
  });
}

export function useUploadActivity(days = 7) {
  return useQuery({
    queryKey: qk.uploadActivity(days),
    queryFn: () => getUploadActivity(days),
  });
}

// Presigned preview URL — only fetched when `enabled` is true (e.g., when
// the dialog opens for a specific file). Kept short-lived (60s) because
// the URL itself has a presigned expiry and is cheap to regenerate.
export function usePreviewUrl(key: string | undefined, enabled: boolean) {
  return useQuery({
    queryKey: qk.preview(key ?? ""),
    queryFn: () => getPreviewUrl(key as string),
    enabled: enabled && !!key,
    staleTime: 60_000,
  });
}

export function useDeleteFile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (fileKey: string) => deleteFile(fileKey),
    // After delete, blow away every cached file list + stats. Cheap and
    // correct — the dashboard re-fetches lazily as components remount.
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.all });
    },
  });
}

// --- Headshot studio ---

export function useStudioStats() {
  return useQuery({ queryKey: qk.studioStats(), queryFn: getStudioStats });
}

export function useStylePacks() {
  return useQuery({
    queryKey: qk.styles(),
    queryFn: getStylePacks,
    staleTime: Infinity, // the registry is static for a given deploy
  });
}

export function useSubjects() {
  return useQuery({ queryKey: qk.subjects(), queryFn: getSubjects });
}

/**
 * Fetches the full subject manifest and — crucially — keeps it live while a
 * background job (captioning / training / generating) is running by polling
 * every 1.5s, stopping the moment the status settles. The manifest on B2 is
 * the single source of truth, so this is what lets the Studio and Gallery
 * reflect "training → trained → complete" transitions and the step/headshot
 * progress counters without a manual refresh.
 */
export function useSubject(id: string | undefined) {
  return useQuery({
    queryKey: qk.subject(id ?? ""),
    queryFn: () => getSubject(id as string),
    enabled: !!id,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && ACTIVE_STATUSES.includes(status) ? 1500 : false;
    },
  });
}

/**
 * Polls the subject's lightweight progress endpoint every 1.5s while a job
 * (captioning / training / generating) is in flight, and stops once it
 * settles. The manifest on B2 is the source of truth — this is pure polling,
 * no websockets.
 */
export function useSubjectProgress(id: string | undefined, enabled = true) {
  return useQuery({
    queryKey: qk.subjectProgress(id ?? ""),
    queryFn: () => getSubjectProgress(id as string),
    enabled: enabled && !!id,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && ACTIVE_STATUSES.includes(status) ? 1500 : false;
    },
  });
}

export function useSubjectGallery(id: string | undefined) {
  return useQuery({
    queryKey: qk.subjectGallery(id ?? ""),
    queryFn: () => getSubjectGallery(id as string),
    enabled: !!id,
  });
}

export function useCreateSubject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => createSubject(name),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.subjects() }),
  });
}

function useSubjectJobMutation<TArgs>(
  fn: (id: string, args: TArgs) => Promise<unknown>,
) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, args }: { id: string; args: TArgs }) => fn(id, args),
    onSuccess: (_data, { id }) => {
      qc.invalidateQueries({ queryKey: qk.subject(id) });
      qc.invalidateQueries({ queryKey: qk.subjectProgress(id) });
    },
  });
}

export function useCaptionSubject() {
  return useSubjectJobMutation<void>((id) => captionSubject(id));
}

export function useTrainSubject() {
  return useSubjectJobMutation<void>((id) => trainSubject(id));
}

export function useGenerateHeadshots() {
  return useSubjectJobMutation<string[]>((id, slugs) =>
    generateHeadshots(id, slugs),
  );
}

export function usePurgeSubject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => purgeSubject(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.all }),
  });
}
