"use client";

import Image from "next/image";

import { Skeleton } from "@/components/ui/skeleton";
import { usePreviewUrl } from "@/lib/queries";
import type { SelfieRef } from "@ai-headshot-studio/shared";

/**
 * Shows each uploaded selfie next to its auto-generated caption. Captions are
 * what the LoRA actually trains against, so making them visible lets the user
 * sanity-check the captioning before kicking off a fine-tune. Thumbnails use
 * the same presigned-preview-URL path as the file browser (no public objects).
 */
export function CaptionList({ selfies }: { selfies: SelfieRef[] }) {
  if (selfies.length === 0) return null;

  const captioned = selfies.filter((s) => s.caption).length;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium text-muted-foreground">Selfies & captions</p>
        <p className="text-xs text-muted-foreground tabular-nums">
          {captioned}/{selfies.length} captioned
        </p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {selfies.map((selfie) => (
          <CaptionCard key={selfie.image_id} selfie={selfie} />
        ))}
      </div>
    </div>
  );
}

function CaptionCard({ selfie }: { selfie: SelfieRef }) {
  const { data } = usePreviewUrl(selfie.key, true);

  return (
    <div className="flex gap-3 rounded-md border border-border p-2">
      <div className="relative h-16 w-16 shrink-0 overflow-hidden rounded bg-muted">
        {data?.url ? (
          <Image
            src={data.url}
            alt={selfie.filename}
            fill
            sizes="64px"
            className="object-cover"
            unoptimized
          />
        ) : (
          <Skeleton className="h-full w-full" />
        )}
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate text-xs font-mono text-muted-foreground">
          {selfie.filename}
        </p>
        {selfie.caption ? (
          <p className="mt-0.5 text-xs leading-snug">{selfie.caption}</p>
        ) : (
          <p className="mt-0.5 text-xs italic text-muted-foreground">
            No caption yet — run Auto-caption.
          </p>
        )}
      </div>
    </div>
  );
}
