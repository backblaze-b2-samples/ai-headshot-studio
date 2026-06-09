import Link from "next/link";
import { Wand2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { SubjectGrid } from "@/components/gallery/subject-grid";

export default function GalleryPage() {
  return (
    <div className="space-y-8">
      <div className="animate-fade-in border-b border-border pb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="page-title">Gallery</h1>
          <p className="text-sm text-muted-foreground mt-1.5">
            Your subjects and their generated headshots, scoped to the{" "}
            <code className="font-mono text-xs">subjects/</code> prefix on B2.
          </p>
        </div>
        <Button asChild size="sm" className="h-8">
          <Link href="/studio">
            <Wand2 className="h-3.5 w-3.5" />
            New headshots
          </Link>
        </Button>
      </div>
      <div className="animate-fade-in-up stagger-2">
        <SubjectGrid />
      </div>
    </div>
  );
}
