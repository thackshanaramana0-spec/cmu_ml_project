import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Academic Copilot",
  description: "Your personal academic second brain",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">
        <nav className="border-b border-neutral-200 dark:border-neutral-800">
          <div className="mx-auto flex max-w-3xl items-center gap-6 px-6 py-4">
            <span className="font-semibold">Academic Copilot</span>
            <div className="flex gap-4 text-sm">
              <Link href="/" className="text-neutral-500 hover:text-neutral-900 dark:hover:text-neutral-100">
                Documents
              </Link>
              <Link href="/chat" className="text-neutral-500 hover:text-neutral-900 dark:hover:text-neutral-100">
                Chat
              </Link>
            </div>
          </div>
        </nav>
        {children}
      </body>
    </html>
  );
}
