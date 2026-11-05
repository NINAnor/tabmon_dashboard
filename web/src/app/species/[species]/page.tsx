import { redirect } from "next/navigation";

// Old per-species URLs (/species/Cuculus_canorus) now live under the Species tab.
export default async function LegacySpeciesPage({ params }: { params: Promise<{ species: string }> }) {
  const { species } = await params;
  redirect(`/species?species=${encodeURIComponent(decodeURIComponent(species).replace(/_/g, " "))}`);
}
