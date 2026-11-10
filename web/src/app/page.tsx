import type { Metadata } from "next";
import { ProjectPage } from "@/components/ProjectPage";
import { PublicShell } from "@/components/SiteHeader";

export const metadata: Metadata = {
  title: "TABMON × BEAGLE · Listening to Europe's birds",
  description:
    "TABMON builds a transnational passive acoustic monitoring network for European birds, from the Arctic to the Mediterranean, continuing within the Horizon Europe project BEAGLE.",
};

export default function Home() {
  return (
    <PublicShell>
      <ProjectPage />
    </PublicShell>
  );
}
