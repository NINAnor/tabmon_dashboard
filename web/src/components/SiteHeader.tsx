"use client";

import { Headphones, Mail } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { CONTACT_URL, labLink } from "@/lib/lab";
import { LanguagePicker } from "./LanguageProvider";

const BEAGLE_URL = "https://cordis.europa.eu/project/id/101288886";

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
        <div className="flex shrink-0 items-center gap-3">
          <Link href="/" className="flex items-center gap-3">
            <img src="/tabmon_logo.png" alt="TABMON" className="h-8 w-auto" />
          </Link>
          <a
            href={BEAGLE_URL}
            target="_blank"
            rel="noreferrer"
            title="BEAGLE · Biodiversity methods for advanced monitoring at large scales"
            className="flex h-10 items-center rounded-md bg-white px-1.5 py-1 hover:ring-2 hover:ring-teal/60"
          >
            <img src="/brand/beagle-logo.png" alt="BEAGLE" className="h-full w-auto" />
          </a>
          <Link href="/" className="hidden items-center gap-3 lg:flex">
            <span className="font-serif text-lg tracking-wide">
              TABMON <span className="text-white/40">×</span> BEAGLE
            </span>
          </Link>
          {variant === "ops" && (
            <span className="rounded-full bg-amber/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-widest text-amber">
              Team
            </span>
          )}
        </div>

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
      <div className="mx-auto max-w-7xl px-6">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-center">
          {/* The positive EU emblem needs a white background. */}
          <div className="shrink-0 self-start rounded-md bg-white p-2">
            <img src="/brand/eu-funded-by-the-eu-small.png" alt="Funded by the European Union" className="h-28 w-auto" />
          </div>
          <div className="space-y-2 text-xs leading-relaxed text-white/50">
            <p>
              BEAGLE has received funding from the European Union&rsquo;s Horizon Europe research and innovation
              programme under grant agreement No 101288886. TABMON was funded through Biodiversa+, the European
              Biodiversity Partnership co-funded by the European Union (grant agreement No 101052342), and national
              funding agencies.
            </p>
            <p className="text-white/35">
              Views and opinions expressed are those of the authors only and do not necessarily reflect those of the
              European Union or the granting authority. Neither the European Union nor the granting authority can be
              held responsible for them.
            </p>
          </div>
        </div>
        <div className="mt-6 flex flex-col items-center justify-between gap-3 border-t border-white/10 pt-6 text-sm text-white/40 md:flex-row">
          <p>
            TABMON · Towards a Transnational Acoustic Biodiversity Monitoring Network ·{" "}
            <a className="hover:text-white" href="https://www.nina.no/">
              NINA
            </a>
          </p>
          <p>Detections by BirdNET, checked by expert and citizen validators.</p>
        </div>
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
