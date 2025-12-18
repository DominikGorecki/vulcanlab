import { MarkdownTabs } from "@/components/markdown/MarkdownTabs";

export default function MarkdownLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Markdown Import/Export</h2>
        <p className="text-muted-foreground">
          Import markdown files or export corpus works as markdown with metadata
        </p>
      </div>

      <MarkdownTabs />

      {children}
    </div>
  );
}
