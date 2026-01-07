"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { LayoutDashboard, Settings, FileText, Eraser, Scissors, Braces, MessageSquare, Database, Zap, FileUp, Trash2, FlaskConical, Search } from "lucide-react";
import { useConversionSettings } from "@/contexts/conversion-settings";

const navItems = [
  { href: "/rag", label: "Research (RAG)", icon: MessageSquare, alwaysVisible: true },
  { href: "/corpus", label: "Corpus", icon: Database, alwaysVisible: true },
  { href: "/simple-conversion", label: "Simple Conversion", icon: Zap, alwaysVisible: true },
  { href: "/conv", label: "Conversion", icon: FileText, alwaysVisible: false },
  { href: "/sanitization", label: "Sanitization", icon: Eraser, alwaysVisible: false },
  { href: "/chunk", label: "Chunking", icon: Scissors, alwaysVisible: false },
  { href: "/vec", label: "Vectorization", icon: Braces, alwaysVisible: true },
  { href: "/search", label: "Search", icon: Search, alwaysVisible: true },
  { href: "/cleanup", label: "Cleanup", icon: Trash2, alwaysVisible: true },
  { href: "/eval", label: "Eval", icon: FlaskConical, alwaysVisible: true },
  { href: "/markdown/export", label: "MD Import/Export", icon: FileUp, alwaysVisible: true },
  { href: "/settings", label: "Settings", icon: Settings, alwaysVisible: true },
];

export function NavBar() {
  const pathname = usePathname();
  const { advancedModeEnabled, loading } = useConversionSettings();

  // Filter nav items based on advanced mode setting
  // During loading, default to hidden (simplified view)
  const visibleNavItems = navItems.filter((item) => {
    if (item.alwaysVisible) return true;
    // Show advanced items only when enabled and not loading
    return !loading && advancedModeEnabled;
  });

  return (
    <div className="flex flex-col w-64 border-r min-h-screen bg-muted/30 sticky top-0 self-start">
      <div className="p-6">
        <div className="flex items-center gap-2">
          <Image
            src="/logo-sm.png"
            alt="VulcanLab Logo"
            width={32}
            height={32}
            className="object-contain"
          />
          <h1 className="text-xl font-bold tracking-tight text-primary">VulcanLab</h1>
        </div>
        <p className="text-xs text-muted-foreground mt-1">v0.6.0</p>
      </div>
      <div className="flex-1 px-4 py-2 space-y-1 overflow-y-auto max-h-[calc(100vh-6rem)]">
        {visibleNavItems.map((item) => {
          const isActive = pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link key={item.href} href={item.href} className="block" data-testid={`nav-item-${item.label.toLowerCase().replace(/\s+/g, '-')}`}>
              <Button
                variant={isActive ? "secondary" : "ghost"}
                className={cn("w-full justify-start", isActive && "font-semibold")}
              >
                <Icon className="mr-2 h-4 w-4" />
                {item.label}
              </Button>
            </Link>
          );
        })}
      </div>
    </div>
  );
}

