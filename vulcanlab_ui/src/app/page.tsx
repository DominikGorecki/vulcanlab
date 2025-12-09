"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
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
      <Card className="w-[400px]">
        <CardHeader>
          <CardTitle>Welcome to VulcanLab</CardTitle>
          <CardDescription>Redirecting to corpus...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex justify-center p-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
