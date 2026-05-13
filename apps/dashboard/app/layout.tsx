import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "MAK Lead Engine",
  description: "Autonomous B2B lead generation pipeline",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body>{children}</body>
    </html>
  );
}
