"use client";

import {
  ArrowRight,
  ArrowUpRight,
  AudioWaveform,
  Bird,
  BrainCircuit,
  Camera,
  Ear,
  Headphones,
  Mail,
  MapPin,
  Mic,
  Moon,
  Network as NetworkIcon,
  Scale,
} from "lucide-react";
import Link from "next/link";
import useSWR from "swr";
import { NetworkStats } from "@/components/Hero";
import { useNetwork } from "@/components/NetworkOverview";
import { fetcher } from "@/lib/api";
import { compact, displayName, int } from "@/lib/format";
import { CONTACT_URL, labLink } from "@/lib/lab";
import { ClipList } from "./ClipPlayer";
import { SpectrogramBackdrop } from "./SpectrogramBackdrop";

const BEAGLE_URL = "https://cordis.europa.eu/project/id/101288886";
const TABMON_PAPER_URL = "https://doi.org/10.1111/2041-210x.70308";

const PRIMER = [
  [
    Bird,
    "Birds announce themselves",
    "Most birds are heard long before they are seen. Each species has its own songs and calls, so a recording tells us who is there, even at night, in fog or in dense forest.",
  ],
  [
    Mic,
    "Recorders listen for us",
    "Passive acoustic monitoring places weatherproof, solar-powered recorders in the field. They listen around the clock and send their audio over the mobile network. No observer needs to be there.",
  ],
  [
    AudioWaveform,
    "Sound becomes a picture",
    "A spectrogram shows time from left to right and pitch from bottom to top; brighter means louder. Songs turn into shapes you learn to recognise, just like a melody.",
  ],
  [
    BrainCircuit,
    "AI listens, people check",
    "BirdNET, a neural network trained on bird sounds, scans every 3 seconds of audio and suggests species with a confidence score. Experts and volunteers check samples to tell us how far each suggestion can be trusted.",
  ],
] as const;

const WHY = [
  [Moon, "Day and night", "Recorders catch nocturnal, shy and secretive birds that surveys often miss."],
  [Ear, "Every season", "Continuous recordings show arrival, song and departure as they happen."],
  [Scale, "At scale", "Autonomous sensors reach remote places at a fraction of the cost of fieldwork."],
  [NetworkIcon, "Comparable", "One protocol from Spain to Norway, so regions can be compared directly."],
] as const;

const EXPLORE = [
  ["/network", "Network", "Where the recorders are, how much we have listened to, and how the data is processed."],
  ["/sites", "Sites", "What does a place sound like? Each cluster's seasonal calendar and daily rhythm of song."],
  ["/species", "Species", "Follow one species from Spain to the Arctic: when it arrives, when it sings and when it leaves."],
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
    url: TABMON_PAPER_URL,
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
  {
    year: 2025,
    title: "TABMON detections dataset",
    venue: "Open data · Zenodo",
    url: "https://doi.org/10.5281/zenodo.17511368",
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
      href={CONTACT_URL}
      className={`inline-flex items-center gap-2 rounded-full border border-white/30 bg-white/5 px-5 py-2.5 text-sm backdrop-blur hover:bg-white/15 ${className}`}
    >
      <Mail className="h-4 w-4" /> Contact
    </a>
  );
}

function Bullet({ children, dot = "bg-white/40" }: { children: React.ReactNode; dot?: string }) {
  return (
    <li className="flex gap-3">
      <span className={`mt-2 h-1.5 w-1.5 shrink-0 rounded-full ${dot}`} />
      <span>{children}</span>
    </li>
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
        <div className="relative mx-auto max-w-7xl px-6 pb-10 pt-20">
          <p className="eyebrow">TABMON × BEAGLE</p>
          <h1 className="mt-3 max-w-3xl font-serif text-4xl leading-tight md:text-6xl">
            A listening network for <span className="italic text-teal">Europe&rsquo;s birds</span>
          </h1>
          <p className="mt-5 max-w-2xl text-lg text-white/70">
            More than a hundred recorders listen day and night along one of Europe&rsquo;s great bird migration
            routes, from the Mediterranean to the Arctic. AI turns their soundscapes into comparable information on
            which birds are present, and when, complementing traditional bird surveys.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              href="/network"
              className="inline-flex items-center gap-2 rounded-full bg-teal px-5 py-2.5 text-sm font-medium text-ocean-950 hover:bg-teal/90"
            >
              Explore the data <ArrowRight className="h-4 w-4" />
            </Link>
            <a
              href={labLink()}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-full bg-amber px-5 py-2.5 text-sm font-medium text-ocean-950 hover:bg-amber/90"
            >
              <Headphones className="h-4 w-4" /> Help identify birds
            </a>
            <ContactButton />
          </div>
          <div className="mt-10">
            <NetworkStats clipsChecked={p?.clips_checked} validated={p?.validated} />
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-7xl px-6">
        {/* Bioacoustics primer */}
        <section className="py-14">
          <p className="eyebrow">New to bioacoustics?</p>
          <h2 className="mt-2 font-serif text-3xl md:text-4xl">Monitoring nature by ear</h2>
          <div className="mt-8 grid gap-10 lg:grid-cols-[1.15fr_1fr]">
            <ol className="grid content-start gap-4 sm:grid-cols-2">
              {PRIMER.map(([Icon, title, text], i) => (
                <li key={title} className="rounded-2xl bg-gradient-to-b from-white/[0.06] to-transparent p-5">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-teal/15">
                      <Icon className="h-5 w-5 text-teal" />
                    </div>
                    <span className="font-serif text-white/35">{i + 1}</span>
                  </div>
                  <p className="mt-4 font-serif text-xl">{title}</p>
                  <p className="mt-1 text-sm text-white/60">{text}</p>
                </li>
              ))}
            </ol>
            <div>
              <div className="card p-5">
                <ClipList species="Cuculus canorus" limit={1} title="Try it · press play" />
                <p className="mt-3 text-sm text-white/55">
                  A Common Cuckoo, recorded by one of our recorders. Its two-note call shows up as two short
                  stripes in the spectrogram; the highlighted window is the 3 seconds BirdNET analysed.
                </p>
              </div>
              <div className="mt-4 rounded-2xl border border-white/10 p-5">
                <p className="font-serif text-lg">What sound can and cannot tell</p>
                <ul className="mt-3 space-y-2 text-sm text-white/60">
                  <Bullet>
                    A detection means a bird was <span className="text-white">calling or singing</span> near the
                    recorder. It measures activity, not how many birds are there.
                  </Bullet>
                  <Bullet>
                    A recorder only hears birds within earshot, and silent birds go unnoticed, so recordings sample
                    a small area around each site.
                  </Bullet>
                  <Bullet>
                    Recorders sometimes stop, so we compare <span className="text-white">detections per hour of
                    recording</span>, never raw totals.
                  </Bullet>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* What we are achieving */}
        <section className="py-14">
          <p className="eyebrow">What we are achieving</p>
          <h2 className="mt-2 font-serif text-3xl md:text-4xl">From a bird network to Europe-wide monitoring</h2>
          <p className="mt-4 max-w-3xl text-white/65">
            Biodiversity is declining, but information on it is patchy and collected unevenly across countries
            and ecosystems. Automated sensors can fill the gaps, provided they are deployed at scale, follow the
            same protocol and produce data that can be trusted and compared.
          </p>
          <div className="relative mt-8 grid gap-6 md:grid-cols-2">
            <div className="absolute left-0 right-0 top-[22px] hidden h-px bg-gradient-to-r from-teal via-teal/60 to-amber md:block" />
            <div className="relative">
              <span className="relative z-10 inline-flex h-11 items-center rounded-full border border-teal/40 bg-ocean-900 px-4 font-serif text-teal">
                2024 → 2026
              </span>
              <div className="card mt-4 flex h-[calc(100%-3.75rem)] flex-col p-6">
                <p className="font-serif text-2xl">TABMON</p>
                <p className="text-sm text-white/50">Biodiversa+ · with national funding agencies</p>
                <p className="mt-3 text-white/65">
                  Built a blueprint for continental-scale acoustic monitoring of birds.
                </p>
                <ul className="mt-4 space-y-2 text-sm text-white/65">
                  <Bullet dot="bg-teal">
                    More than 100 recorders in Norway, the Netherlands, France and Spain, placed along a
                    continental bird migration route.
                  </Bullet>
                  <Bullet dot="bg-teal">
                    Audio recorded continuously and uploaded in near real time.
                  </Bullet>
                  <Bullet dot="bg-teal">
                    An automated AI pipeline, with expert and citizen validation that calibrates how far each
                    species&rsquo; detections can be trusted.
                  </Bullet>
                  <Bullet dot="bg-teal">
                    Data for Essential Biodiversity Variables, such as when species are active and where they
                    occur, shared openly with this dashboard.
                  </Bullet>
                </ul>
                <a
                  href={TABMON_PAPER_URL}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-auto inline-flex items-center gap-1 pt-5 text-sm text-teal hover:underline"
                >
                  Read the network paper <ArrowUpRight className="h-3.5 w-3.5" />
                </a>
              </div>
            </div>
            <div className="relative">
              <span className="relative z-10 inline-flex h-11 items-center rounded-full border border-amber/50 bg-ocean-900 px-4 font-serif text-amber">
                Oct 2026 → Sep 2030
              </span>
              <div className="card mt-4 flex h-[calc(100%-3.75rem)] flex-col border-amber/30 bg-amber/[0.04] p-6">
                <p className="font-serif text-2xl">BEAGLE</p>
                <p className="text-sm text-white/50">
                  Horizon Europe · 17 partners · coordinated by Aarhus University
                </p>
                <p className="mt-3 text-white/65">
                  <span className="text-white">Biodiversity methods for advanced monitoring at large scales</span>{" "}
                  takes this approach to all of nature, on land, in freshwater and at sea.
                </p>
                <ul className="mt-4 space-y-2 text-sm text-white/65">
                  <Bullet dot="bg-amber">
                    Over a thousand sensors, thousands of eDNA samples, AI and citizen science, producing up to
                    a billion species records.
                  </Bullet>
                  <Bullet dot="bg-amber">
                    Harmonised, open biodiversity indicators supporting the EU Biodiversity Strategy for 2030,
                    the Nature Restoration Regulation and the Kunming-Montreal Global Biodiversity Framework.
                  </Bullet>
                  <Bullet dot="bg-amber">
                    The TABMON network continues and grows, joined by{" "}
                    <Camera className="mb-0.5 inline h-3.5 w-3.5" /> camera traps and automated moth traps, so
                    that birds, mammals and insects can be followed at the same places.
                  </Bullet>
                </ul>
                <a
                  href={BEAGLE_URL}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-auto inline-flex items-center gap-1 pt-5 text-sm text-amber hover:underline"
                >
                  BEAGLE on CORDIS <ArrowUpRight className="h-3.5 w-3.5" />
                </a>
              </div>
            </div>
          </div>
          <div className="mt-8 grid gap-4 md:grid-cols-4">
            {WHY.map(([Icon, title, text]) => (
              <div key={title} className="flex gap-3">
                <Icon className="mt-1 h-5 w-5 shrink-0 text-teal" />
                <div>
                  <p className="font-serif text-lg">{title}</p>
                  <p className="text-sm text-white/55">{text}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Explore the data */}
        <section className="py-14">
          <p className="eyebrow">Explore the data</p>
          <h2 className="mt-2 font-serif text-3xl md:text-4xl">See what the recorders hear</h2>
          <ul className="mt-6 grid gap-4 md:grid-cols-3">
            {EXPLORE.map(([href, title, text]) => (
              <li key={href}>
                <Link
                  href={href}
                  className="group flex h-full flex-col rounded-2xl border border-white/10 p-6 hover:border-teal/40 hover:bg-white/[0.04]"
                >
                  <span className="flex items-center justify-between font-serif text-2xl group-hover:text-teal">
                    {title}
                    <ArrowRight className="h-5 w-5 text-white/30 transition group-hover:translate-x-1 group-hover:text-teal" />
                  </span>
                  <span className="mt-2 text-sm text-white/60">{text}</span>
                </Link>
              </li>
            ))}
          </ul>
          <p className="mt-4 flex items-center gap-2 text-xs text-white/40">
            <MapPin className="h-3.5 w-3.5" /> Public maps show locations generalised to about 10 km.
          </p>
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
                      <span className="font-serif text-3xl text-amber">{compact(p.clips_checked ?? p.validated)}</span>
                      <span className="ml-2 text-sm text-white/55">{p.clips_checked ? "clips checked" : "detections checked"}</span>
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
          <p className="mt-3 max-w-3xl text-white/60">
            TABMON brings together research institutes, universities and bird monitoring organisations in four
            countries. BEAGLE widens the collaboration to{" "}
            <a href={BEAGLE_URL} target="_blank" rel="noreferrer" className="text-amber hover:underline">
              17 partners across Europe
            </a>
            .
          </p>
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
          <p className="eyebrow">Publications & open data</p>
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
