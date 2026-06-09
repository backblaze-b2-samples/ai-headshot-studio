"use client";

import Image from "next/image";
import { Download } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { StyleSection as StyleSectionData } from "@ai-headshot-studio/shared";

export function StyleSection({ section }: { section: StyleSectionData }) {
  return (
    <section className="space-y-3">
      <div className="flex items-baseline justify-between border-b border-border pb-2">
        <h3 className="text-sm font-semibold">{section.style.label}</h3>
        <span className="text-xs text-muted-foreground font-mono">
          {section.headshots.length} images
        </span>
      </div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
        {section.headshots.map((shot) => (
          <div
            key={shot.key}
            className="group relative aspect-square overflow-hidden rounded-md border border-border bg-muted"
          >
            <Image
              src={shot.url}
              alt={`${section.style.label} headshot ${shot.index + 1}`}
              fill
              sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 25vw"
              className="object-cover transition-transform group-hover:scale-105"
              unoptimized
            />
            <a
              href={shot.url}
              download
              className="absolute inset-0 flex items-end justify-end p-2 opacity-0 transition-opacity group-hover:opacity-100"
            >
              <Button size="icon" variant="secondary" className="h-7 w-7" asChild>
                <span>
                  <Download className="h-3.5 w-3.5" />
                </span>
              </Button>
            </a>
          </div>
        ))}
      </div>
    </section>
  );
}
