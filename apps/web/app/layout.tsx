import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Memory Refactor",
  description: "Typed memory refactor dashboard",
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
