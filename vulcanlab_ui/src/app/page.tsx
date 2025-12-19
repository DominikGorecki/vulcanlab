"use client";

import { PageLoadingState } from "@/components";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function Home() {
  const router = useRouter();

  // Redirect to Corpus page on load
  useEffect(() => {
    router.push("/corpus");
  }, [router]);

  return (
    <div className="flex items-center justify-center h-full">
      <PageLoadingState
        title="Welcome to VulcanLab"
        description="Redirecting to corpus..."
      />
    </div>
  );
}
