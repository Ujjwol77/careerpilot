import type { Metadata } from "next";
import Script from "next/script";
import "./globals.css";
import { themeInitScript } from "@/components/themeScript";

export const metadata: Metadata = {
  title: "CareerPilot: multi-agent career platform",
  description: "Upload your CV, find matching jobs, close skill gaps and practise interviews with collaborating AI agents.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        {/* beforeInteractive: Next.js puts this in <head> and runs it before the page paints, so a saved theme never flashes */}
        <Script id="theme-init" strategy="beforeInteractive">{themeInitScript}</Script>
        {children}
      </body>
    </html>
  );
}
