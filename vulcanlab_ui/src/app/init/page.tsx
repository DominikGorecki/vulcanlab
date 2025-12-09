"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function InitRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to settings page with init tab selected
    router.replace("/settings?tab=init");
  }, [router]);

  return null;
}
