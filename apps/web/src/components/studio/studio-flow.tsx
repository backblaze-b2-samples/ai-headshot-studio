"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { Sparkles, Wand2, Images, Loader2 } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { SelfieStep } from "@/components/studio/selfie-step";
import { CaptionList } from "@/components/studio/caption-list";
import { StylePicker } from "@/components/studio/style-picker";
import { SubjectStatusBadge } from "@/components/studio/status-badge";
import {
  useCaptionSubject,
  useCreateSubject,
  useGenerateHeadshots,
  useSubject,
  useTrainSubject,
} from "@/lib/queries";
import type { Subject } from "@ai-headshot-studio/shared";

function StepCard({
  index,
  title,
  children,
}: {
  index: number;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <Card>
      <CardHeader className="border-b border-border py-4 px-5">
        <CardTitle className="card-title flex items-center gap-2">
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-foreground text-background text-[11px] font-bold">
            {index}
          </span>
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="p-5">{children}</CardContent>
    </Card>
  );
}

export function StudioFlow() {
  const router = useRouter();
  // Deep-link support: /studio?subjectId=… loads an existing subject straight
  // into the flow (e.g. "Generate more" from a trained subject's gallery)
  // instead of forcing the user to define a brand-new subject.
  const searchParams = useSearchParams();
  const [name, setName] = useState("");
  const [subjectId, setSubjectId] = useState<string | null>(
    () => searchParams.get("subjectId"),
  );
  const [styles, setStyles] = useState<string[]>([]);

  const createSubject = useCreateSubject();
  const caption = useCaptionSubject();
  const train = useTrainSubject();
  const generate = useGenerateHeadshots();

  // useSubject self-polls while a job runs, so the UI tracks the
  // training → trained → complete transitions and the progress counters live.
  const { data: subject } = useSubject(subjectId ?? undefined);

  const s: Subject | undefined = subject;
  const busy =
    s?.status === "captioning" ||
    s?.status === "training" ||
    s?.status === "generating";

  const onCreate = async () => {
    try {
      const created = await createSubject.mutateAsync(name.trim());
      setSubjectId(created.id);
      toast.success(`Subject "${created.name}" created`);
    } catch {
      toast.error("Could not create subject");
    }
  };

  const toggleStyle = (slug: string) =>
    setStyles((prev) =>
      prev.includes(slug) ? prev.filter((x) => x !== slug) : [...prev, slug],
    );

  const trainPct = s?.train_steps_total
    ? Math.round((s.train_steps_done / s.train_steps_total) * 100)
    : 0;
  const genPct = s?.headshots_total
    ? Math.round((s.headshots_done / s.headshots_total) * 100)
    : 0;

  // --- Step 1: name the subject (only when there is no subject at all) ---
  if (!subjectId) {
    return (
      <StepCard index={1} title="Name your subject">
        <div className="flex flex-col gap-3 sm:flex-row">
          <Input
            placeholder="e.g. Jordan's headshots"
            value={name}
            onChange={(e) => setName(e.target.value)}
            maxLength={80}
            onKeyDown={(e) => e.key === "Enter" && name.trim() && onCreate()}
          />
          <Button onClick={onCreate} disabled={!name.trim() || createSubject.isPending}>
            {createSubject.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4" />
            )}
            Start
          </Button>
        </div>
      </StepCard>
    );
  }

  // A subject is selected (just created or deep-linked) but not loaded yet.
  if (!s) {
    return <Skeleton className="h-64 w-full" />;
  }

  const canCaption = s.selfies.length >= 4;
  const canTrain =
    s.status === "ready_to_train" || s.status === "trained" || s.status === "complete";
  const canGenerate =
    (s.status === "trained" || s.status === "complete") && styles.length > 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">{s.name}</h2>
          <p className="text-xs text-muted-foreground font-mono">
            {s.selfies.length} selfies · {s.headshots.length} headshots
          </p>
        </div>
        <SubjectStatusBadge status={s.status} />
      </div>

      <StepCard index={2} title="Upload selfies">
        <SelfieStep subjectId={s.id} disabled={busy} />
      </StepCard>

      <StepCard index={3} title="Caption & train">
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Auto-caption the selfies, then fine-tune a likeness LoRA. Training runs
            on Backblaze-stored data and writes the model back to B2.
          </p>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              disabled={!canCaption || busy}
              onClick={() =>
                caption.mutate(
                  { id: s.id, args: undefined },
                  { onError: () => toast.error("Captioning failed") },
                )
              }
            >
              Auto-caption ({s.selfies.length})
            </Button>
            <Button
              disabled={!canTrain || busy}
              onClick={() =>
                train.mutate(
                  { id: s.id, args: undefined },
                  {
                    onSuccess: () => toast.info("Training started"),
                    onError: () => toast.error("Could not start training"),
                  },
                )
              }
            >
              <Wand2 className="h-4 w-4" />
              Train likeness
            </Button>
          </div>
          {s.status === "training" && (
            <div className="space-y-1">
              <Progress value={trainPct} className="h-1.5 progress-gradient" />
              <p className="text-xs text-muted-foreground tabular-nums">
                Training… {s.train_steps_done}/{s.train_steps_total} steps ({trainPct}%)
              </p>
            </div>
          )}
          <CaptionList selfies={s.selfies} />
          {s.error && <p className="text-xs text-destructive">{s.error}</p>}
        </div>
      </StepCard>

      <StepCard index={4} title="Pick style packs & generate">
        <div className="space-y-4">
          <StylePicker selected={styles} onToggle={toggleStyle} disabled={busy} />
          <div className="flex flex-wrap items-center gap-3">
            <Button
              disabled={!canGenerate || busy}
              onClick={() =>
                generate.mutate(
                  { id: s.id, args: styles },
                  {
                    onSuccess: () => toast.info("Generating headshots"),
                    onError: () => toast.error("Could not start generation"),
                  },
                )
              }
            >
              <Images className="h-4 w-4" />
              Generate headshots
            </Button>
            {(s.status === "complete" || s.headshots.length > 0) && (
              <Button variant="outline" onClick={() => router.push(`/gallery/${s.id}`)}>
                View gallery
              </Button>
            )}
          </div>
          {s.status === "generating" && (
            <div className="space-y-1">
              <Progress value={genPct} className="h-1.5 progress-gradient" />
              <p className="text-xs text-muted-foreground tabular-nums">
                Rendering… {s.headshots_done}/{s.headshots_total} headshots ({genPct}%)
              </p>
            </div>
          )}
        </div>
      </StepCard>
    </div>
  );
}
