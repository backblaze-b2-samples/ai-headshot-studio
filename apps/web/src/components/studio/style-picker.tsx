"use client";

import { Check } from "lucide-react";
import { useStylePacks } from "@/lib/queries";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface StylePickerProps {
  selected: string[];
  onToggle: (slug: string) => void;
  disabled?: boolean;
}

export function StylePicker({ selected, onToggle, disabled }: StylePickerProps) {
  const { data: packs, isLoading } = useStylePacks();

  if (isLoading || !packs) {
    return (
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-20 w-full" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {packs.map((pack) => {
        const isOn = selected.includes(pack.slug);
        return (
          <button
            key={pack.slug}
            type="button"
            disabled={disabled}
            onClick={() => onToggle(pack.slug)}
            aria-pressed={isOn}
            className={cn(
              "relative text-left rounded-md border p-3 transition-colors",
              isOn
                ? "border-primary bg-[var(--accent-subtle)]"
                : "border-border hover:border-primary/60 hover:bg-muted/60",
              disabled && "opacity-50 cursor-not-allowed",
            )}
          >
            {isOn && (
              <span className="absolute right-2 top-2 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-primary-foreground">
                <Check className="h-3 w-3" />
              </span>
            )}
            <p className="text-sm font-semibold">{pack.label}</p>
            <p className="mt-1 text-xs text-muted-foreground">{pack.description}</p>
          </button>
        );
      })}
    </div>
  );
}
