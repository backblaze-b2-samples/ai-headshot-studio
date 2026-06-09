import { Badge } from "@/components/ui/badge";
import type { SubjectStatus } from "@ai-headshot-studio/shared";

const LABELS: Record<SubjectStatus, string> = {
  created: "Collecting selfies",
  captioning: "Captioning",
  ready_to_train: "Ready to train",
  training: "Training",
  trained: "Model ready",
  generating: "Generating",
  complete: "Complete",
  failed: "Failed",
};

const VARIANTS: Record<SubjectStatus, "default" | "secondary" | "outline" | "destructive"> = {
  created: "outline",
  captioning: "secondary",
  ready_to_train: "outline",
  training: "secondary",
  trained: "default",
  generating: "secondary",
  complete: "default",
  failed: "destructive",
};

export function SubjectStatusBadge({ status }: { status: SubjectStatus }) {
  return <Badge variant={VARIANTS[status]}>{LABELS[status]}</Badge>;
}
