"use client";

import { useRouter } from "next/navigation";
import { Trash2, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { usePurgeSubject } from "@/lib/queries";

/** Right-to-be-forgotten: a real batch delete of every B2 object under
 *  subjects/{id}/ — selfies, captions, the trained LoRA, and all headshots. */
export function PurgeDialog({
  subjectId,
  subjectName,
}: {
  subjectId: string;
  subjectName: string;
}) {
  const router = useRouter();
  const purge = usePurgeSubject();

  const onConfirm = () => {
    purge.mutate(subjectId, {
      onSuccess: (res) => {
        toast.success(
          `Purged "${subjectName}" — ${res.objects_deleted} objects deleted from B2.`,
        );
        router.push("/gallery");
      },
      onError: () => toast.error("Failed to purge subject"),
    });
  };

  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <Button variant="outline" size="sm" className="text-destructive border-destructive/40">
          <Trash2 className="h-3.5 w-3.5" />
          Delete subject
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete this subject and all face data?</AlertDialogTitle>
          <AlertDialogDescription>
            This permanently removes every object under{" "}
            <code className="font-mono text-xs">subjects/{subjectId}/</code> on
            Backblaze B2 — the uploaded selfies, their captions, the trained likeness
            model, and every generated headshot. This cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            disabled={purge.isPending}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {purge.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            Delete everything
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
