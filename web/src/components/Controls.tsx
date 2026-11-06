"use client";

export function YearToggle({
  years,
  value,
  onChange,
}: {
  years: number[];
  value: number | null;
  onChange: (year: number | null) => void;
}) {
  return (
    <div className="inline-flex rounded-full border border-white/15 p-0.5 text-xs">
      {[null, ...years].map((y) => (
        <button
          key={y ?? "all"}
          onClick={() => onChange(y)}
          className={`rounded-full px-3 py-1 transition-colors ${
            value === y ? "bg-teal text-ocean-950" : "text-white/65 hover:text-white"
          }`}
        >
          {y ?? "All years"}
        </button>
      ))}
    </div>
  );
}

export function Segmented<T extends string>({
  options,
  value,
  onChange,
  titles,
}: {
  options: [T, string][];
  value: T;
  onChange: (v: T) => void;
  titles?: Record<string, string>;
}) {
  return (
    <div className="inline-flex rounded-full border border-white/15 p-0.5 text-xs">
      {options.map(([v, label]) => (
        <button
          key={v}
          title={titles?.[v]}
          onClick={() => onChange(v)}
          className={`rounded-full px-3 py-1 transition-colors ${
            value === v ? "bg-white/90 text-ocean-950" : "text-white/65 hover:text-white"
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
