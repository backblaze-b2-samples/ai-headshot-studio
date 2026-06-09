import { StudioFlow } from "@/components/studio/studio-flow";

export default function StudioPage() {
  return (
    <div className="space-y-8">
      <div className="animate-fade-in border-b border-border pb-5">
        <h1 className="page-title">Studio</h1>
        <p className="text-sm text-muted-foreground mt-1.5">
          Upload selfies, fine-tune a likeness, and generate professional headshots
          across curated style packs. Every artifact lands on Backblaze B2.
        </p>
      </div>
      <div className="animate-fade-in-up stagger-2">
        <StudioFlow />
      </div>
    </div>
  );
}
