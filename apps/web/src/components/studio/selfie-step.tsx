"use client";

import { useCallback, useState } from "react";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import type { FileRejection } from "react-dropzone";
import { Camera } from "lucide-react";

import { Dropzone } from "@/components/upload/dropzone";
import { UploadProgress, type UploadItem } from "@/components/upload/upload-progress";
import { uploadSelfie } from "@/lib/api-client";
import { qk } from "@/lib/queries";

interface SelfieStepProps {
  subjectId: string;
  disabled?: boolean;
}

/** Selfie ingestion — reuses the generic Dropzone but routes uploads to the
 *  subject-scoped /subjects/{id}/selfies endpoint. */
export function SelfieStep({ subjectId, disabled }: SelfieStepProps) {
  const qc = useQueryClient();
  const [items, setItems] = useState<UploadItem[]>([]);

  const handleRejected = useCallback((rejections: FileRejection[]) => {
    for (const r of rejections) {
      toast.error(`${r.file.name}: ${r.errors.map((e) => e.message).join(", ")}`);
    }
  }, []);

  const handleSelected = useCallback(
    (files: File[]) => {
      const next: UploadItem[] = files.map((file) => ({
        id: `${file.name}-${Date.now()}-${Math.random()}`,
        file,
        progress: 0,
        status: "uploading" as const,
      }));
      setItems((prev) => [...prev, ...next]);

      void (async () => {
        for (const item of next) {
          try {
            await uploadSelfie(subjectId, item.file, (pct) =>
              setItems((prev) =>
                prev.map((i) => (i.id === item.id ? { ...i, progress: pct } : i)),
              ),
            );
            setItems((prev) =>
              prev.map((i) =>
                i.id === item.id ? { ...i, status: "complete", progress: 100 } : i,
              ),
            );
          } catch (err) {
            const message = err instanceof Error ? err.message : "Upload failed";
            setItems((prev) =>
              prev.map((i) =>
                i.id === item.id ? { ...i, status: "error", error: message } : i,
              ),
            );
            toast.error(`${item.file.name}: ${message}`);
          }
        }
        qc.invalidateQueries({ queryKey: qk.subject(subjectId) });
      })();
    },
    [subjectId, qc],
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Camera className="h-4 w-4" />
        Add 4–20 clear selfies — varied angles and lighting train a better likeness.
      </div>
      <Dropzone
        onFilesSelected={handleSelected}
        onFilesRejected={handleRejected}
        disabled={disabled}
      />
      <UploadProgress items={items} />
    </div>
  );
}
