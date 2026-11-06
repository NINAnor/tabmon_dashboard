const LISTENING_LAB_URL = process.env.NEXT_PUBLIC_LISTENING_LAB_URL ?? "https://tabmon-listening-lab.nina.no";

/** Calibration needs at least this many validated clips per species. */
export const MIN_VALIDATIONS = 20;

/** Deep link into the Listening Lab citizen app, preselecting what we know. */
export function labLink(opts: { country?: string | null; cluster?: string | null; species?: string | null } = {}) {
  const params = new URLSearchParams();
  if (opts.country) params.set("country", opts.country);
  if (opts.cluster) params.set("cluster", opts.cluster);
  if (opts.species) params.set("species", opts.species);
  const q = params.toString();
  return q ? `${LISTENING_LAB_URL}/?${q}` : LISTENING_LAB_URL;
}

export const CONTACT_URL = "mailto:benjamin.cretois@nina.no?subject=TABMON";
