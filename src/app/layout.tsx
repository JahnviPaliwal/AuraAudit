import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Intercompany Settlement Controller",
  description: "Automated multi-entity ledger reconciliation and period-close controller dashboard.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
