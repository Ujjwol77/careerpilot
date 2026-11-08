import type { Metadata } from "next";
import "./globals.css";
import { themeInitScript } from "@/components/themeScript";

export const metadata: Metadata = {
  title: "CareerPilot: multi-agent career platform",
  description: "Upload your CV, find matching jobs, close skill gaps and practise interviews with collaborating AI agents.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body>{children}</body>
    </html>
  );
}
