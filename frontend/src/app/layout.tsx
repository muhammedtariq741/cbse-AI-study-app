import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "CBSE Study App | AI-Powered Class 9 Study Assistant",
  description: "Get board exam-ready answers with our AI-powered study assistant. NCERT-aligned, marking scheme optimized for CBSE Class 9 students.",
  keywords: ["CBSE", "Class 9", "Study App", "NCERT", "Board Exam", "AI Tutor"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className} suppressHydrationWarning>{children}</body>
    </html>
  );
}
