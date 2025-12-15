"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { LayoutDashboard, Settings, FileText, Eraser, Scissors, Braces, MessageSquare, Database, Zap } from "lucide-react";

const navItems = [
  { href: "/corpus", label: "Corpus", icon: Database },
  { href: "/conv", label: "Conversion", icon: FileText },
  { href: "/simple-conversion", label: "Simple Conversion", icon: Zap },
  { href: "/sanitization", label: "Sanitization", icon: Eraser },
  { href: "/chunk", label: "Chunking", icon: Scissors },
  { href: "/vec", label: "Vectorization", icon: Braces },
  { href: "/rag", label: "RAG", icon: MessageSquare },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function NavBar() {
  const pathname = usePathname();

  return (
    <div className="flex flex-col w-64 border-r min-h-screen bg-muted/30 sticky top-0 self-start">
      <div className="p-6">
        <h1 className="text-xl font-bold tracking-tight text-primary">VulcanLab</h1>
        <p className="text-xs text-muted-foreground mt-1">v0.1.1</p>
      </div>
      <div className="flex-1 px-4 py-2 space-y-1 overflow-y-auto max-h-[calc(100vh-6rem)]">
        {navItems.map((item) => {
          const isActive = pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link key={item.href} href={item.href} className="block">
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

