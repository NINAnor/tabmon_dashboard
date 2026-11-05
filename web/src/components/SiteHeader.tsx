"use client";

import { Headphones } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { labLink } from "@/lib/lab";

const PUBLIC_TABS = [
  ["/", "Network"],
  ["/sites", "Sites"],
  ["/species", "Species"],
  ["/project", "Project"],
] as const;

const OPS_LINKS = [
  ["/ops", "Devices"],
  ["/ops/activity", "Activity"],
  ["/ops/dataset", "Dataset"],
  ["/ops/sites", "Sites"],
  ["/ops/validation", "Validation"],
] as const;

export function SiteHeader({ variant = "public" }: { variant?: "public" | "ops" }) {
  const pathname = usePathname();
  const links = variant === "public" ? PUBLIC_TABS : OPS_LINKS;
  const isActive = (href: string) =>
    href === "/" || href === "/ops" ? pathname === href : pathname.startsWith(href);

  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-white/5 bg-ocean-900/80 backdrop-blur-md">
      <nav className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-6">
        <Link href="/" className="flex shrink-0 items-center gap-3">
          <img src="/tabmon_logo.png" alt="TABMON" className="h-8 w-auto" />
          <span className="hidden font-serif text-lg tracking-wide sm:inline">TABMON</span>
          {variant === "ops" && (
            <span className="rounded-full bg-amber/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-widest text-amber">
              Team
            </span>
          )}
        </Link>

        <div className="flex min-w-0 items-center gap-1 overflow-x-auto rounded-full border border-white/10 bg-white/[0.03] p-1 text-sm">
          {links.map(([href, label]) => (
            <Link
              key={href}
              href={href}
              className={`whitespace-nowrap rounded-full px-4 py-1.5 transition-colors ${
                isActive(href) ? "bg-teal text-ocean-950" : "text-white/70 hover:text-white"
              }`}
            >
              {label}
            </Link>
          ))}
        </div>

        <div className="flex shrink-0 items-center gap-2">
          {variant === "public" && (
            <a
              href={labLink()}
              target="_blank"
              rel="noreferrer"
              className="hidden items-center gap-1.5 rounded-full bg-amber px-3.5 py-1.5 text-xs font-medium text-ocean-950 hover:bg-amber/90 md:inline-flex"
              title="Listen to recordings and confirm what BirdNET heard"
            >
              <Headphones className="h-3.5 w-3.5" /> Help identify birds
            </a>
          )}
          <Link href={variant === "public" ? "/ops" : "/"} className="pill">
            {variant === "public" ? "Team area" : "Public site"}
          </Link>
        </div>
      </nav>
    </header>
  );
}

export function Footer() {
  return (
    <footer className="border-t border-white/10 py-10">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-3 px-6 text-sm text-white/40 md:flex-row">
        <p>
          TABMON · Towards a Transnational Acoustic Biodiversity Monitoring Network ·{" "}
          <a className="hover:text-white" href="https://www.nina.no/english/TABMON">
            NINA
          </a>
        </p>
        <p>Detections by BirdNET, checked by expert and citizen validators.</p>
      </div>
    </footer>
  );
}

export function PublicShell({ children }: { children: React.ReactNode }) {
  return (
    <>
      <SiteHeader />
      <main className="min-h-screen pt-16">{children}</main>
      <Footer />
    </>
  );
}
