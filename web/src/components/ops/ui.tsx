"use client";

export function PageTitle({ eyebrow, title, children }: { eyebrow: string; title: string; children?: React.ReactNode }) {
  return (
    <div className="mb-8">
      <p className="eyebrow">{eyebrow}</p>
      <h1 className="mt-2 font-serif text-4xl">{title}</h1>
      {children && <div className="mt-2 max-w-3xl text-sm text-white/55">{children}</div>}
    </div>
  );
}

export function Stat({ label, value, sub, tone }: { label: string; value: React.ReactNode; sub?: string; tone?: "good" | "bad" }) {
  return (
    <div className="card px-5 py-4">
      <p className="eyebrow">{label}</p>
      <p className={`mt-2 font-serif text-3xl tabular-nums ${tone === "good" ? "text-teal" : tone === "bad" ? "text-coral" : ""}`}>
        {value}
      </p>
      {sub && <p className="mt-1 text-xs text-white/45">{sub}</p>}
    </div>
  );
}

export function StatusDot({ status }: { status: string }) {
  const online = status === "Online";
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={`h-2 w-2 rounded-full ${online ? "bg-teal shadow-[0_0_8px_#4ecdc4]" : "bg-coral"}`} />
      {status}
    </span>
  );
}
