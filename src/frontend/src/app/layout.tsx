import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "BaaS Orchestrator",
  description: "Enterprise Blockchain-as-a-Service Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        {/* Decorative background blobs */}
        <div className="fixed top-0 -z-10 h-full w-full overflow-hidden">
          <div className="absolute -top-[10%] -left-[10%] w-[50%] h-[50%] rounded-full bg-blue-600/20 blur-[120px]" />
          <div className="absolute top-[40%] -right-[10%] w-[40%] h-[60%] rounded-full bg-purple-600/20 blur-[120px]" />
          <div className="absolute -bottom-[20%] left-[20%] w-[60%] h-[40%] rounded-full bg-indigo-600/20 blur-[120px]" />
        </div>
        {children}
      </body>
    </html>
  );
}
