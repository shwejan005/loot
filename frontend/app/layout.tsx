import type { Metadata, Viewport } from "next";
import { League_Spartan } from "next/font/google";
import "./globals.css";

const leagueSpartan = League_Spartan({
  subsets: ["latin"],
  variable: "--font-league-spartan",
  display: "swap",
  weight: ["400", "500", "600", "700", "800", "900"],
});

export const metadata: Metadata = {
  title: "Loot Wallet — Money, made smarter",
  description:
    "Your AI-powered financial co-pilot. Track rewards, spot savings, and make every purchase count.",
  applicationName: "Loot Wallet",
  keywords: ["Loot Wallet", "rewards", "cashback", "spending insights"],
  manifest: "/manifest.webmanifest",
  appleWebApp: {
    capable: true,
    title: "Loot Wallet",
    statusBarStyle: "default",
  },
  icons: {
    icon: "/icon.svg",
    shortcut: "/icon.svg",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: "#721e3b",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={leagueSpartan.variable}>
      <body>{children}</body>
    </html>
  );
}
