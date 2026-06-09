"use client";

import { useMemo } from "react";
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts";
import { PieChart } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  type ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { useStudioStats } from "@/lib/queries";

const LABELS: Record<string, string> = {
  selfies: "Selfies",
  captions: "Captions",
  models: "Models",
  headshots: "Headshots",
  other: "Other",
};

const chartConfig = {
  mb: { label: "MB", color: "var(--chart-1)" },
} satisfies ChartConfig;

export function StorageBreakdown() {
  const { data: stats, error, refetch } = useStudioStats();

  const data = useMemo(
    () =>
      (stats?.breakdown ?? []).map((slice) => ({
        category: LABELS[slice.category] ?? slice.category,
        mb: +(slice.size_bytes / (1024 * 1024)).toFixed(2),
        objects: slice.object_count,
      })),
    [stats],
  );

  return (
    <Card>
      <CardHeader className="border-b border-border py-4 px-5">
        <CardTitle className="card-title">Storage by Artifact</CardTitle>
        <CardDescription className="text-xs">
          Megabytes on B2 under the subjects/ prefix
        </CardDescription>
      </CardHeader>
      <CardContent className="p-5">
        {error ? (
          <ErrorState error={error} onRetry={() => refetch()} />
        ) : data.length === 0 ? (
          <EmptyState
            icon={PieChart}
            title="No artifacts yet"
            description="Create a subject and generate headshots to see storage usage."
          />
        ) : (
          <ChartContainer config={chartConfig} className="h-[240px] w-full">
            <BarChart data={data} margin={{ top: 8, right: 4, left: -16, bottom: 0 }}>
              <defs>
                <linearGradient id="storage-fill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--color-mb)" stopOpacity={0.95} />
                  <stop offset="100%" stopColor="var(--color-mb)" stopOpacity={0.55} />
                </linearGradient>
              </defs>
              <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="category" tickLine={false} axisLine={false} tickMargin={10} fontSize={11} />
              <YAxis tickLine={false} axisLine={false} tickMargin={6} fontSize={11} width={32} />
              <ChartTooltip cursor={{ fill: "var(--accent-subtle)" }} content={<ChartTooltipContent />} />
              <Bar dataKey="mb" fill="url(#storage-fill)" radius={[4, 4, 0, 0]} animationDuration={500} />
            </BarChart>
          </ChartContainer>
        )}
      </CardContent>
    </Card>
  );
}
