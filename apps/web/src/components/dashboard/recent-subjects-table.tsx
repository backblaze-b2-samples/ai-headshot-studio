"use client";

import Link from "next/link";
import { ArrowRight, Inbox } from "lucide-react";
import { Card, CardAction, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { SubjectStatusBadge } from "@/components/studio/status-badge";
import { useSubjects } from "@/lib/queries";
import { formatDate } from "@/lib/utils";

export function RecentSubjectsTable() {
  const { data: subjects = [], isLoading, error, refetch } = useSubjects();
  const recent = subjects.slice(0, 8);

  return (
    <Card>
      <CardHeader className="border-b border-border py-4 px-5">
        <CardTitle className="card-title">Recent Subjects</CardTitle>
        <CardAction className="self-center">
          <Link
            href="/gallery"
            className="inline-flex items-center gap-1 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            View all
            <ArrowRight className="h-3 w-3" />
          </Link>
        </CardAction>
      </CardHeader>
      <CardContent className="p-0">
        {isLoading ? (
          <div className="p-4 space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : error ? (
          <ErrorState error={error} onRetry={() => refetch()} />
        ) : recent.length === 0 ? (
          <EmptyState
            icon={Inbox}
            title="No subjects yet"
            description="Head to the Studio to create your first headshots."
          />
        ) : (
          <Table className="table-fixed">
            <TableHeader>
              <TableRow className="bg-muted/40 hover:bg-muted/40">
                <TableHead className="w-[40%] text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Subject
                </TableHead>
                <TableHead className="w-[18%] text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Headshots
                </TableHead>
                <TableHead className="w-[22%] text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Created
                </TableHead>
                <TableHead className="w-[20%] text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Status
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {recent.map((subject) => (
                <TableRow key={subject.id} className="table-row-hover">
                  <TableCell className="font-medium">
                    <Link href={`/gallery/${subject.id}`} className="truncate hover:underline">
                      {subject.name}
                    </Link>
                  </TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground tabular-nums">
                    {subject.headshot_count}
                  </TableCell>
                  <TableCell className="text-muted-foreground whitespace-nowrap">
                    {formatDate(subject.created_at)}
                  </TableCell>
                  <TableCell className="whitespace-nowrap">
                    <SubjectStatusBadge status={subject.status} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
