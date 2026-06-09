"use client";

import Link from "next/link";
import { Images, UserPlus } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Button } from "@/components/ui/button";
import { SubjectStatusBadge } from "@/components/studio/status-badge";
import { useSubjects } from "@/lib/queries";
import { formatDate } from "@/lib/utils";

export function SubjectGrid() {
  const { data: subjects = [], isLoading, error, refetch } = useSubjects();

  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-32 w-full" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-0">
          <ErrorState error={error} onRetry={() => refetch()} />
        </CardContent>
      </Card>
    );
  }

  if (subjects.length === 0) {
    return (
      <EmptyState
        icon={Images}
        title="No subjects yet"
        description="Create a subject in the Studio to start generating headshots."
        action={
          <Button asChild size="sm">
            <Link href="/studio">
              <UserPlus className="h-3.5 w-3.5" />
              Open Studio
            </Link>
          </Button>
        }
      />
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {subjects.map((subject) => (
        <Link key={subject.id} href={`/gallery/${subject.id}`}>
          <Card className="card-hover h-full">
            <CardContent className="p-4 space-y-3">
              <div className="flex items-start justify-between gap-2">
                <p className="font-semibold truncate">{subject.name}</p>
                <SubjectStatusBadge status={subject.status} />
              </div>
              <p className="text-xs text-muted-foreground font-mono">
                {subject.selfie_count} selfies · {subject.headshot_count} headshots
              </p>
              <p className="text-xs text-muted-foreground">
                {formatDate(subject.created_at)}
              </p>
            </CardContent>
          </Card>
        </Link>
      ))}
    </div>
  );
}
