"use client";

import { Headphones, Mail } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { CONTACT_URL, labLink } from "@/lib/lab";
import { LanguagePicker } from "./LanguageProvider";

const PUBLIC_TABS = [
  ["/", "Project"],
  ["/network", "Network"],
  ["/sites", "Sites"],
  ["/species", "Species"],
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
      <nav className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-x-4 gap-y-2 px-6 py-2 md:h-16 md:flex-nowrap md:py-0">
        <Link href="/" className="flex shrink-0 items-center gap-3">
          <img src="/tabmon_logo.png" alt="TABMON" className="h-8 w-auto" />
          <span className="hidden font-serif text-lg tracking-wide lg:inline">
            TABMON <span className="text-white/40">×</span> BEAGLE
          </span>
          {variant === "ops" && (
            <span className="rounded-full bg-amber/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-widest text-amber">
              Team
            </span>
          )}
        </Link>

        <div className="order-last flex w-full min-w-0 items-center justify-between gap-1 overflow-x-auto rounded-full border border-white/10 bg-white/[0.03] p-1 text-sm md:order-none md:w-auto md:justify-start">
          {links.map(([href, label]) => (
            <Link
              key={href}
              href={href}
              className={`flex-1 whitespace-nowrap rounded-full px-3 py-1.5 text-center transition-colors md:flex-none md:px-4 ${
                isActive(href) ? "bg-teal text-ocean-950" : "text-white/70 hover:text-white"
              }`}
            >
              {label}
            </Link>
          ))}
        </div>

        <div className="flex shrink-0 items-center gap-2">
          {variant === "public" && (
            <>
              <a
                href={labLink()}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 rounded-full bg-amber px-2.5 py-1.5 text-xs font-medium text-ocean-950 hover:bg-amber/90 md:px-3.5"
                title="Listen to recordings and confirm what BirdNET heard"
              >
                <Headphones className="h-3.5 w-3.5" /> <span className="hidden md:inline">Help identify birds</span>
              </a>
              <a href={CONTACT_URL} className="pill" title="Email the TABMON team">
                <Mail className="h-3.5 w-3.5" /> <span className="hidden md:inline">Contact</span>
              </a>
            </>
          )}
          <LanguagePicker />
          <Link href={variant === "public" ? "/ops" : "/"} className="pill">
            {variant === "public" ? "Team area" : "Public site"}
          </Link>
        </div>
      </nav>
    </header>
  );
}

function Footer() {
  return (
    <footer className="border-t border-white/10 py-10">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-3 px-6 text-sm text-white/40 md:flex-row">
        <p>
          TABMON · Towards a Transnational Acoustic Biodiversity Monitoring Network ·{" "}
          <a className="hover:text-white" href="https://www.nina.no/">
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
      <main className="min-h-screen pt-28 md:pt-16">{children}</main>
      <Footer />
    </>
  );
}
