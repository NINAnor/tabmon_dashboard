import type { Metadata } from "next";
import { ProjectPage } from "@/components/ProjectPage";
import { PublicShell } from "@/components/SiteHeader";

export const metadata: Metadata = {
  title: "Project · TABMON",
  description:
    "TABMON builds a transnational passive acoustic monitoring network for European birds, from the Arctic to the Mediterranean.",
};

export default function Project() {
  return (
    <PublicShell>
      <ProjectPage />
    </PublicShell>
  );
}
