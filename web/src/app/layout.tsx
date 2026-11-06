import type { Metadata } from "next";
import { Inter, Playfair_Display } from "next/font/google";
import "maplibre-gl/dist/maplibre-gl.css";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const playfair = Playfair_Display({ subsets: ["latin"], variable: "--font-playfair" });

export const metadata: Metadata = {
  title: "TABMON × BEAGLE · Listening to Europe's birds",
  description:
    "Acoustic monitoring of bird migration across Europe, from Spain to Arctic Norway.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${playfair.variable}`}>
      <body className="min-h-screen bg-ocean-900">{children}</body>
    </html>
  );
}
