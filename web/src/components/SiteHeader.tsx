import Link from "next/link";

export function SiteHeader({ variant = "public" }: { variant?: "public" | "ops" }) {
  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-white/5 bg-ocean-900/70 backdrop-blur-md">
      <nav className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <Link href="/" className="flex items-center gap-3">
          <img src="/tabmon_logo.png" alt="TABMON" className="h-8 w-auto" />
          <span className="font-serif text-lg tracking-wide">TABMON</span>
          {variant === "ops" && (
            <span className="rounded-full bg-amber/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-widest text-amber">
              Team
            </span>
          )}
        </Link>
        <div className="flex items-center gap-1 text-sm text-white/70">
          {variant === "public" ? (
            <>
              <a href="#phenology" className="rounded-full px-3 py-1.5 hover:text-white">
                Migration
              </a>
              <a href="#places" className="rounded-full px-3 py-1.5 hover:text-white">
                Places
              </a>
              <a href="#species" className="rounded-full px-3 py-1.5 hover:text-white">
                Species
              </a>
              <Link href="/ops" className="pill ml-2">
                Team area
              </Link>
            </>
          ) : (
            <OpsNav />
          )}
        </div>
      </nav>
    </header>
  );
}

const OPS_LINKS = [
  ["/ops", "Devices"],
  ["/ops/activity", "Activity"],
  ["/ops/dataset", "Dataset"],
  ["/ops/sites", "Sites"],
  ["/ops/validation", "Validation"],
] as const;

function OpsNav() {
  return (
    <>
      {OPS_LINKS.map(([href, label]) => (
        <Link key={href} href={href} className="rounded-full px-3 py-1.5 hover:text-white">
          {label}
        </Link>
      ))}
      <Link href="/" className="pill ml-2">
        Public site
      </Link>
    </>
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
