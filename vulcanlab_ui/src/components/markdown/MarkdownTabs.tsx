"use client";

import { usePathname, useRouter } from "next/navigation";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";

export function MarkdownTabs() {
  const pathname = usePathname();
  const router = useRouter();

  // Determine active tab based on current pathname
  const activeTab = pathname.startsWith("/markdown/import") ? "import" : "export";

  const handleTabChange = (value: string) => {
    router.push(`/markdown/${value}`);
  };

  return (
    <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
      <TabsList>
        <TabsTrigger value="export" data-testid="markdown-tab-export">
          Export
        </TabsTrigger>
        <TabsTrigger value="import" data-testid="markdown-tab-import">
          Import
        </TabsTrigger>
      </TabsList>
    </Tabs>
  );
}
