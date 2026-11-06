import { format } from "d3-format";

export const COUNTRY_COLORS: Record<string, string> = {
  Norway: "#7fb8ff",
  Netherlands: "#f4b860",
  France: "#c39bff",
  Spain: "#ff7a6b",
};

export const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export const compact = (n: number | null | undefined) =>
  n === null || n === undefined ? "–" : format(".3~s")(n).replace("G", "B");

export const int = (n: number | null | undefined) =>
  n === null || n === undefined ? "–" : format(",d")(Math.round(n));

export const pct = (n: number | null | undefined, digits = 1) =>
  n === null || n === undefined ? "–" : `${(n * 100).toFixed(digits)}%`;

export const rate = (n: number | null | undefined) =>
  n === null || n === undefined ? "–" : n < 10 ? n.toFixed(2) : n.toFixed(1);

export function displayName(s: { species: string; common_en?: string | null }) {
  return s.common_en || s.species;
}

export function weekLabel(weekStarts: string[], week: number) {
  const d = new Date(weekStarts[week - 1]);
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

export function relativeDays(days: number | null) {
  if (days === null || days === undefined) return "–";
  if (days < 1) return `${Math.round(days * 24)} h ago`;
  return `${Math.round(days)} d ago`;
}
