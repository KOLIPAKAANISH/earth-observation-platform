import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Change Detection Demo",
  description: "Satellite change-detection demo (DEMO DATA)",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-slate-100">{children}</body>
    </html>
  );
}
