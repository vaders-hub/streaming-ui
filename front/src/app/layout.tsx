import type { Metadata } from "next";
import "./globals.css";
import { GNB } from "@/components/GNB";

export const metadata: Metadata = {
  title: "SSE Streaming UI",
  description: "Real-time data streaming with Server-Sent Events",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen bg-gradient-to-b from-background to-muted/20">
        <GNB />
        <main>{children}</main>
      </body>
    </html>
  );
}
