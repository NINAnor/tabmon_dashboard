"use client";

import { ArrowRight, ArrowUpRight, Clock, Headphones, Mail, Moon, Network as NetworkIcon, Scale } from "lucide-react";
import Link from "next/link";
import useSWR from "swr";
import { useNetwork } from "@/components/NetworkOverview";
import { fetcher } from "@/lib/api";
import { compact, displayName, int } from "@/lib/format";
import { labLink } from "@/lib/lab";
import { SpectrogramBackdrop } from "./SpectrogramBackdrop";

const CONTACT = "mailto:benjamin.cretois@nina.no?subject=TABMON";
const BEAGLE_URL = "https://cordis.europa.eu/project/id/101288886";

const WHY = [
  [Moon, "Day and night", "Recorders listen around the clock, catching nocturnal and secretive birds."],
  [Clock, "Every season", "Continuous recordings reveal arrival, song and departure as they happen."],
  [Scale, "At scale", "Autonomous, solar-powered sensors reach remote landscapes cheaply."],
  [NetworkIcon, "Comparable", "One protocol from Spain to Norway, so regions can be compared directly."],
] as const;

const PARTNERS = [
  ["NINA", "Norwegian Institute for Nature Research", "Norway", "https://www.nina.no/"],
  ["Naturalis", "Naturalis Biodiversity Center", "Netherlands", "https://www.naturalis.nl/"],
  ["UvA", "University of Amsterdam – IBED", "Netherlands", "https://ibed.uva.nl/"],
  ["Tilburg", "Tilburg University", "Netherlands", "https://www.tilburguniversity.edu/"],
  ["CBS", "Statistics Netherlands", "Netherlands", "https://www.cbs.nl/"],
  ["Sovon", "Sovon Vogelonderzoek Nederland", "Netherlands", "https://www.sovon.nl/"],
  ["LIS", "Université de Toulon – LIS", "France", "https://www.lis-lab.fr/"],
  ["CTFC", "Forest Science and Technology Centre of Catalonia", "Spain", "https://www.ctfc.cat/"],
] as const;

const PUBLICATIONS = [
  {
    year: 2026,
    title: "TABMON: Design and deployment of a transnational passive acoustic monitoring network for European birds",
    venue: "Methods in Ecology and Evolution",
    url: "https://besjournals.onlinelibrary.wiley.com/doi/full/10.1111/2041-210x.70308",
  },
  {
    year: 2026,
    title: "Data-driven sampling strategies for fine-tuning bird detection models",
    venue: "Journal of the Acoustical Society of America",
    url: "https://pubs.aip.org/asa/jasa/article/159/6/4891/3393438",
  },
  {
    year: 2025,
    title: "Stratified active learning for spatiotemporal generalisation in large-scale bioacoustic monitoring",
    venue: "bioRxiv preprint",
    url: "https://doi.org/10.1101/2025.09.01.673472",
  },
];

type Wanted = {
  species: string;
  common_en: string | null;
  n_detections: number;
  n_validated: number;
  needed: number;
  country: string;
  cluster: string;
};

function ContactButton({ className = "" }: { className?: string }) {
  return (
    <a
      href={CONTACT}
      className={`inline-flex items-center gap-2 rounded-full border border-white/30 bg-white/5 px-5 py-2.5 text-sm backdrop-blur hover:bg-white/15 ${className}`}
    >
      <Mail className="h-4 w-4" /> Contact
    </a>
  );
}

export function ProjectPage() {
  const { data: network } = useNetwork();
  const { data: wanted } = useSWR<Wanted[]>("/api/public/most-wanted?limit=5", fetcher);
  const p = network?.pipeline;

  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_#123044_0%,_#07131c_60%)]" />
        <SpectrogramBackdrop />
        <div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-ocean-900 to-transparent" />
        <div className="relative mx-auto max-w-7xl px-6 pb-16 pt-20">
          <p className="eyebrow">The project</p>
          <h1 className="mt-3 max-w-3xl font-serif text-4xl leading-tight md:text-6xl">
            A listening network for <span className="italic text-teal">Europe&rsquo;s birds</span>
          </h1>
          <p className="mt-5 max-w-2xl text-lg text-white/70">
            TABMON places autonomous recorders from the Mediterranean to the Arctic and uses AI to turn their
            soundscapes into comparable biodiversity indicators, complementing traditional bird surveys.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <ContactButton />
            <a
              href={labLink()}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-full bg-amber px-5 py-2.5 text-sm font-medium text-ocean-950 hover:bg-amber/90"
            >
              <Headphones className="h-4 w-4" /> Help identify birds
            </a>
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-7xl px-6">
        {/* Why */}
        <section className="grid gap-4 py-6 md:grid-cols-4">
          {WHY.map(([Icon, title, text]) => (
            <div key={title} className="rounded-2xl bg-gradient-to-b from-white/[0.06] to-transparent p-5">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-teal/15">
                <Icon className="h-5 w-5 text-teal" />
              </div>
              <p className="mt-4 font-serif text-xl">{title}</p>
              <p className="mt-1 text-sm text-white/55">{text}</p>
            </div>
          ))}
        </section>

        {/* Timeline: TABMON -> BEAGLE */}
        <section className="py-14">
          <p className="eyebrow">Funding</p>
          <h2 className="mt-2 font-serif text-3xl md:text-4xl">From TABMON to BEAGLE</h2>
          <div className="relative mt-8 grid gap-6 md:grid-cols-2">
            <div className="absolute left-0 right-0 top-[22px] hidden h-px bg-gradient-to-r from-teal via-teal/60 to-amber md:block" />
            <div className="relative">
              <span className="relative z-10 inline-flex h-11 items-center rounded-full border border-teal/40 bg-ocean-900 px-4 font-serif text-teal">
                2024 → 2026
              </span>
              <div className="card mt-4 p-6">
                <p className="font-serif text-2xl">TABMON</p>
                <p className="text-sm text-white/50">Biodiversa+ · with national funding agencies</p>
                <p className="mt-3 text-white/65">
                  Designed and deployed the network: more than 100 recorders in Norway, the Netherlands, France and
                  Spain, the AI pipeline, and the validation tools behind this dashboard.
                </p>
              </div>
            </div>
            <div className="relative">
              <span className="relative z-10 inline-flex h-11 items-center rounded-full border border-amber/50 bg-ocean-900 px-4 font-serif text-amber">
                Oct 2026 → 2030
              </span>
              <a
                href={BEAGLE_URL}
                target="_blank"
                rel="noreferrer"
                className="card group mt-4 block border-amber/30 bg-amber/[0.04] p-6 hover:bg-amber/[0.08]"
              >
                <p className="flex items-center justify-between font-serif text-2xl">
                  BEAGLE
                  <ArrowUpRight className="h-5 w-5 text-amber/60 group-hover:text-amber" />
                </p>
                <p className="text-sm text-white/50">Horizon Europe · coordinated by Aarhus University</p>
                <p className="mt-3 text-white/65">
                  The network continues within <span className="text-white">BEAGLE</span>, Biodiversity methods for
                  advanced monitoring at large scales: 17 partners combining sensors, eDNA, AI and citizen science
                  to deliver harmonised biodiversity indicators across Europe.
                </p>
              </a>
            </div>
          </div>
        </section>

        {/* Take part */}
        <section className="py-14">
          <div className="overflow-hidden rounded-3xl border border-amber/25 bg-gradient-to-br from-amber/[0.10] via-ocean-800 to-ocean-900">
            <div className="grid gap-8 p-8 md:p-10 lg:grid-cols-[1.1fr_1fr]">
              <div>
                <p className="eyebrow text-amber/80">Take part</p>
                <h2 className="mt-2 font-serif text-3xl md:text-4xl">Lend us your ears</h2>
                <p className="mt-4 text-white/70">
                  BirdNET is good, but not perfect. In the Listening Lab you hear short clips from our recorders and
                  say whether the suggested bird is really there. Each answer sets the confidence threshold used by
                  every chart on this site.
                </p>
                {p && (
                  <p className="mt-5 flex flex-wrap gap-x-6 gap-y-2">
                    <span>
                      <span className="font-serif text-3xl text-amber">{compact(p.validated)}</span>
                      <span className="ml-2 text-sm text-white/55">clips checked</span>
                    </span>
                    <span>
                      <span className="font-serif text-3xl text-amber">{p.calibrated}</span>
                      <span className="ml-2 text-sm text-white/55">species calibrated</span>
                    </span>
                  </p>
                )}
                <a
                  href={labLink()}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-7 inline-flex items-center gap-2 rounded-full bg-amber px-6 py-3 text-sm font-medium text-ocean-950 hover:bg-amber/90"
                >
                  <Headphones className="h-4 w-4" /> Open the Listening Lab
                </a>
              </div>
              <div>
                <p className="eyebrow">Most wanted · often heard, rarely checked</p>
                <ul className="mt-3 space-y-2">
                  {wanted?.map((w) => (
                    <li key={w.species}>
                      <a
                        href={labLink({ country: w.country, cluster: w.cluster, species: w.species })}
                        target="_blank"
                        rel="noreferrer"
                        className="group flex items-center gap-3 rounded-xl bg-ocean-950/50 px-4 py-3 hover:bg-ocean-950/80"
                      >
                        <span className="min-w-0 flex-1">
                          <span className="block truncate">{displayName(w)}</span>
                          <span className="text-xs text-white/45">
                            {compact(w.n_detections)} detections · {int(w.n_validated)} checked
                          </span>
                        </span>
                        <span className="shrink-0 text-xs text-amber/80 group-hover:text-amber">
                          {w.needed} needed <ArrowRight className="inline h-3 w-3" />
                        </span>
                      </a>
                    </li>
                  ))}
                  {!wanted && <li className="h-56 animate-pulse rounded-xl bg-white/5" />}
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Partners */}
        <section className="py-14">
          <p className="eyebrow">Partners</p>
          <h2 className="mt-2 font-serif text-3xl md:text-4xl">A European consortium</h2>
          <ul className="mt-6 grid grid-cols-2 gap-3 md:grid-cols-4">
            {PARTNERS.map(([short, name, country, url]) => (
              <li key={short}>
                <a
                  href={url}
                  target="_blank"
                  rel="noreferrer"
                  className="group flex h-full flex-col rounded-2xl border border-white/10 p-4 hover:border-white/25 hover:bg-white/[0.04]"
                >
                  <span className="font-serif text-2xl group-hover:text-teal">{short}</span>
                  <span className="mt-1 text-xs text-white/55">{name}</span>
                  <span className="mt-auto pt-2 text-[11px] uppercase tracking-wider text-white/35">{country}</span>
                </a>
              </li>
            ))}
          </ul>
        </section>

        {/* Publications */}
        <section className="py-14">
          <p className="eyebrow">Publications</p>
          <h2 className="mt-2 font-serif text-3xl md:text-4xl">Selected research</h2>
          <ul className="mt-6 divide-y divide-white/10 border-y border-white/10">
            {PUBLICATIONS.map((pub) => (
              <li key={pub.title}>
                <a href={pub.url} target="_blank" rel="noreferrer" className="group flex items-baseline gap-5 py-4">
                  <span className="font-serif text-white/35">{pub.year}</span>
                  <span className="flex-1">
                    <span className="block group-hover:text-teal">{pub.title}</span>
                    <span className="text-sm italic text-white/45">{pub.venue}</span>
                  </span>
                  <ArrowUpRight className="h-4 w-4 shrink-0 text-white/30 group-hover:text-teal" />
                </a>
              </li>
            ))}
          </ul>
        </section>

        {/* Closing contact */}
        <section className="pb-20 pt-6 text-center">
          <p className="font-serif text-2xl">Questions, data requests or collaboration ideas?</p>
          <ContactButton className="mt-5" />
          <p className="mt-6 text-xs text-white/35">
            Coordinated by the Norwegian Institute for Nature Research (NINA) · Funded by{" "}
            <a href="https://www.biodiversa.eu/" target="_blank" rel="noreferrer" className="hover:text-white">
              Biodiversa+
            </a>{" "}
            and{" "}
            <a href={BEAGLE_URL} target="_blank" rel="noreferrer" className="hover:text-white">
              Horizon Europe (BEAGLE)
            </a>
          </p>
        </section>
      </div>
    </>
  );
}
