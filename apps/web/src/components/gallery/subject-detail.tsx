"use client";

import Link from "next/link";
import { ArrowLeft, Images } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { SubjectStatusBadge } from "@/components/studio/status-badge";
import { StyleSection } from "@/components/gallery/style-section";
import { PurgeDialog } from "@/components/gallery/purge-dialog";
import {
  useSubject,
  useSubjectGallery,
  useSubjectProgress,
} from "@/lib/queries";

export function SubjectDetail({ subjectId }: { subjectId: string }) {
  const { data: subject, isLoading, error, refetch } = useSubject(subjectId);
  // Live progress while a job runs; also refreshes the subject + gallery.
  useSubjectProgress(subjectId, true);
  const { data: sections = [] } = useSubjectGallery(subjectId);

  if (isLoading) return <Skeleton className="h-64 w-full" />;
  if (error) {
    return (
      <Card>
        <CardContent className="p-0">
          <ErrorState error={error} onRetry={() => refetch()} />
        </CardContent>
      </Card>
    );
  }
  if (!subject) return null;

  const trainPct = subject.train_steps_total
    ? Math.round((subject.train_steps_done / subject.train_steps_total) * 100)
    : 0;
  const genPct = subject.headshots_total
    ? Math.round((subject.headshots_done / subject.headshots_total) * 100)
    : 0;

  return (
    <div className="space-y-8">
      <div className="animate-fade-in border-b border-border pb-5">
        <Link
          href="/gallery"
          className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors mb-3"
        >
          <ArrowLeft className="h-3 w-3" />
          All subjects
        </Link>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <h1 className="page-title">{subject.name}</h1>
              <SubjectStatusBadge status={subject.status} />
            </div>
            <p className="text-sm text-muted-foreground font-mono">
              {subject.selfies.length} selfies · {subject.headshots.length} headshots ·{" "}
              {subject.generator_provider} engine
            </p>
          </div>
          <div className="flex gap-2">
            <Button asChild variant="outline" size="sm">
              <Link href="/studio">Generate more</Link>
            </Button>
            <PurgeDialog subjectId={subject.id} subjectName={subject.name} />
          </div>
        </div>
      </div>

      {subject.status === "training" && (
        <div className="space-y-1">
          <Progress value={trainPct} className="h-1.5 progress-gradient" />
          <p className="text-xs text-muted-foreground tabular-nums">
            Training likeness… {trainPct}%
          </p>
        </div>
      )}
      {subject.status === "generating" && (
        <div className="space-y-1">
          <Progress value={genPct} className="h-1.5 progress-gradient" />
          <p className="text-xs text-muted-foreground tabular-nums">
            Rendering headshots… {subject.headshots_done}/{subject.headshots_total} ({genPct}%)
          </p>
        </div>
      )}
      {subject.error && (
        <p className="text-sm text-destructive">{subject.error}</p>
      )}

      {sections.length === 0 ? (
        <EmptyState
          icon={Images}
          title="No headshots yet"
          description="Train the likeness and generate a style pack from the Studio."
        />
      ) : (
        <div className="space-y-8 animate-fade-in-up stagger-2">
          {sections.map((section) => (
            <StyleSection key={section.style.slug} section={section} />
          ))}
        </div>
      )}
    </div>
  );
}
