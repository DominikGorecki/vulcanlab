"use client";

import { ConversionSettingsProvider } from "@/contexts/conversion-settings";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ConversionSettingsProvider>
      {children}
    </ConversionSettingsProvider>
  );
}
