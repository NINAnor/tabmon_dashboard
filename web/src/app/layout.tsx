import type { Metadata } from "next";
import { Playfair_Display } from "next/font/google";
import "maplibre-gl/dist/maplibre-gl.css";
import "./globals.css";
import { LanguageProvider } from "@/components/LanguageProvider";

const playfair = Playfair_Display({ subsets: ["latin"], variable: "--font-playfair" });

export const metadata: Metadata = {
  title: "TABMON × BEAGLE · Listening to Europe's birds",
  description:
    "Acoustic monitoring of bird migration across Europe, from Spain to Arctic Norway.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={playfair.variable}>
      <body className="min-h-screen bg-ocean-900">
        <LanguageProvider>{children}</LanguageProvider>
      </body>
    </html>
  );
}
