import { useEffect, useMemo, useState } from "react";

const API_BASE =
  import.meta.env.VITE_API_BASE ??
  (import.meta.env.DEV ? "http://localhost:5000/api" : "/api");

const fallbackProducts = [
  {
    id: 101,
    name: "Wraith X1",
    category: "Ready-To-Game",
    description: "1080p esports rocket with headroom for streaming.",
    price: 999,
    gpu: "RTX 4060",
    cpu: "Ryzen 5 7600",
    memory: "16GB DDR5",
    storage: "1TB NVMe Gen4",
    use_case: "Esports / Creator Starter",
    badge: "Best Value",
    image: "https://images.unsplash.com/photo-1545239351-1141bd82e8a6?auto=format&fit=crop&w=1200&q=80",
  },
  {
    id: 102,
    name: "Nebula Pro",
    category: "Creator",
    description: "4K-capable workstation tuned for Adobe + Blender.",
    price: 1999,
    gpu: "RTX 4070 Ti Super",
    cpu: "Ryzen 7 7800X3D",
    memory: "32GB DDR5",
    storage: "2TB NVMe Gen4",
    use_case: "4K Video / 3D",
    badge: "Creator Pick",
    image: "https://images.unsplash.com/photo-1484704849700-f032a568e944?auto=format&fit=crop&w=1200&q=80",
  },
  {
    id: 103,
    name: "Titan Apex",
    category: "Enthusiast",
    description: "Maxed-out thermals, liquid cooled, VR-ready, AI capable.",
    price: 3299,
    gpu: "RTX 4090",
    cpu: "Intel i9-14900K",
    memory: "64GB DDR5",
    storage: "2TB NVMe Gen4 + 4TB SSD",
    use_case: "VR / AI / 8K",
    badge: "Flagship",
    image: "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=1200&q=80",
  },
];

const fallbackFaqs = [
  {
    id: 1,
    question: "How long does it take to build and ship?",
    answer:
      "Most ready-to-ship builds leave our lab in 3 business days. Custom requests average 7–10 business days.",
  },
  {
    id: 2,
    question: "Do you offer warranty and support?",
    answer:
      "Every WhatAPC system includes a 2-year parts and labor warranty plus lifetime chat support.",
  },
  {
    id: 3,
    question: "Can I upgrade later?",
    answer:
      "Absolutely. We design with standard parts and roomy cases. We can also handle upgrades for you.",
  },
];

const perks = [
  { title: "Thermals First", body: "Hand-built airflow, burn-in, and cable-managed for future upgrades." },
  { title: "Zero Bloat", body: "Clean OS images, tuned BIOS profiles, and stress-tested drivers." },
  { title: "Lifetime Support", body: "Chat with builders, not bots. Remote diagnostics included." },
  { title: "Transparent Pricing", body: "No mystery SKUs. You see every part in your build sheet." },
];

function Stat({ label, value }) {
  return (
    <div className="flex flex-col gap-1 rounded-xl border border-slate-800 bg-slate-900/60 px-4 py-3">
      <span className="text-sm uppercase tracking-wide text-slate-400">{label}</span>
      <span className="text-2xl font-semibold text-cyan-300">{value}</span>
    </div>
  );
}

function ProductCard({ product }) {
  return (
    <div className="group flex flex-col rounded-2xl border border-slate-800 bg-slate-900/70 p-6 shadow-xl shadow-cyan-900/20 transition hover:-translate-y-1 hover:border-cyan-500/60 hover:shadow-cyan-700/30">
      {product.image && (
        <div className="mb-4 overflow-hidden rounded-xl border border-slate-800/80 bg-slate-950">
          <img
            src={product.image}
            alt={product.name}
            className="h-40 w-full object-cover transition duration-500 group-hover:scale-105"
            loading="lazy"
          />
        </div>
      )}
      <div className="flex items-center justify-between">
        <div className="text-sm uppercase tracking-wide text-cyan-300/80">{product.category}</div>
        {product.badge && (
          <span className="rounded-full bg-cyan-500/10 px-3 py-1 text-xs font-semibold text-cyan-200">
            {product.badge}
          </span>
        )}
      </div>
      <h3 className="mt-3 text-xl font-semibold text-white">{product.name}</h3>
      <p className="mt-2 text-sm text-slate-300">{product.description}</p>
      <div className="mt-4 grid grid-cols-2 gap-3 text-sm text-slate-200">
        <span className="rounded-lg bg-slate-800/70 px-3 py-2">CPU: {product.cpu}</span>
        <span className="rounded-lg bg-slate-800/70 px-3 py-2">GPU: {product.gpu}</span>
        <span className="rounded-lg bg-slate-800/70 px-3 py-2">RAM: {product.memory}</span>
        <span className="rounded-lg bg-slate-800/70 px-3 py-2">Storage: {product.storage}</span>
      </div>
      <div className="mt-6 flex items-center justify-between">
        <div>
          <p className="text-sm text-slate-400">Starts at</p>
          <p className="text-3xl font-bold text-white">${product.price.toLocaleString()}</p>
        </div>
        <button className="rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 px-4 py-2 text-sm font-semibold text-slate-900 transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-400">
          View Build Sheet
        </button>
      </div>
    </div>
  );
}

function FAQ({ item }) {
  return (
    <details className="group rounded-xl border border-slate-800 bg-slate-900/60 p-4">
      <summary className="cursor-pointer list-none text-base font-semibold text-white">
        <span className="text-cyan-300 group-open:text-cyan-200">Q.</span> {item.question}
      </summary>
      <p className="mt-3 text-sm leading-relaxed text-slate-300">{item.answer}</p>
    </details>
  );
}

function App() {
  const [products, setProducts] = useState(fallbackProducts);
  const [faqs, setFaqs] = useState(fallbackFaqs);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", budget: "", primary_use: "", preferences: "" });
  const [formStatus, setFormStatus] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [productsRes, faqsRes] = await Promise.all([
          fetch(`${API_BASE}/products`),
          fetch(`${API_BASE}/faqs`),
        ]);
        if (productsRes.ok) setProducts(await productsRes.json());
        if (faqsRes.ok) setFaqs(await faqsRes.json());
      } catch (error) {
        console.warn("API unreachable, using fallback data.", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const heroStats = useMemo(
    () => [
      { label: "Avg. Ship Time", value: "3-5 business days" },
      { label: "Pass Rate (Burn-In)", value: "99.4%" },
      { label: "Support Rating", value: "4.9/5" },
      { label: "States Served", value: "All 50" },
    ],
    []
  );

  const handleSubmit = async (event) => {
    event.preventDefault();
    setFormStatus("sending");
    try {
      const res = await fetch(`${API_BASE}/custom-builds`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...form, budget: Number(form.budget) || null }),
      });

      if (!res.ok) throw new Error("Request failed");

      setFormStatus("success");
      setForm({ name: "", email: "", budget: "", primary_use: "", preferences: "" });
    } catch (error) {
      console.error(error);
      setFormStatus("error");
    }
  };

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-16 px-6 pb-20 pt-12 sm:px-10 lg:px-12">
      <header className="flex flex-col gap-6 rounded-3xl border border-slate-800 bg-slate-950/70 p-8 shadow-lg shadow-cyan-900/20 backdrop-blur">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500 to-blue-700 text-lg font-extrabold text-slate-950 shadow-lg shadow-cyan-800/40">
              WA
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-cyan-300">WhatAPC</p>
              <h1 className="text-2xl font-bold text-white">Precision-built PCs, zero fuss.</h1>
            </div>
          </div>
          <div className="flex gap-3">
            <a
              className="rounded-lg border border-slate-800 px-4 py-2 text-sm font-semibold text-slate-200 transition hover:border-cyan-400/70 hover:text-white"
              href="#catalog"
            >
              Ready Builds
            </a>
            <a
              className="rounded-lg bg-gradient-to-r from-cyan-400 to-blue-600 px-4 py-2 text-sm font-semibold text-slate-900 transition hover:brightness-105"
              href="#custom"
            >
              Start Custom Build
            </a>
          </div>
        </div>
        <div className="grid gap-6 lg:grid-cols-[1.2fr,0.8fr]">
          <div className="space-y-5">
            <p className="inline-flex rounded-full bg-cyan-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-cyan-200">
              Built in the USA · Ships fast nationwide
            </p>
            <h2 className="text-4xl font-extrabold leading-tight text-white sm:text-5xl">
              Custom gaming and creator PCs without the mystery markup.
            </h2>
            <p className="text-lg text-slate-300">
              Pick a proven configuration or tell us how you play, stream, or create. We’ll deliver a thermally-balanced,
              cable-managed build with transparent parts and lifetime support.
            </p>
            <div className="flex flex-wrap gap-3">
              {perks.slice(0, 3).map((perk) => (
                <div key={perk.title} className="rounded-lg border border-slate-800/80 bg-slate-900/70 px-3 py-2 text-sm text-slate-200">
                  {perk.title}
                </div>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {heroStats.map((stat) => (
              <Stat key={stat.label} label={stat.label} value={stat.value} />
            ))}
          </div>
        </div>
      </header>

      <section id="catalog" className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-cyan-300">Ready-to-ship lineup</p>
            <h3 className="text-2xl font-semibold text-white">Curated builds for every lane</h3>
          </div>
          {loading && <span className="text-sm text-slate-400">Syncing inventory…</span>}
        </div>
        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {products.map((p) => (
            <ProductCard key={p.id} product={p} />
          ))}
        </div>
      </section>

      <section className="space-y-6 rounded-3xl border border-slate-800 bg-gradient-to-r from-slate-900 via-slate-900 to-slate-950 p-8 shadow-inner shadow-cyan-900/30">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-cyan-300">Why WhatAPC</p>
            <h3 className="text-2xl font-semibold text-white">Built by enthusiasts, documented like a business</h3>
          </div>
          <span className="rounded-full bg-cyan-500/10 px-3 py-1 text-xs font-semibold text-cyan-200">
            Lifetime tune-ups
          </span>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {perks.map((perk) => (
            <div
              key={perk.title}
              className="rounded-xl border border-slate-800/80 bg-slate-950/60 p-4 shadow-md shadow-slate-900/50"
            >
              <p className="text-sm font-semibold text-white">{perk.title}</p>
              <p className="mt-2 text-sm text-slate-300">{perk.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section
        id="custom"
        className="grid gap-8 rounded-3xl border border-slate-800 bg-slate-900/70 p-8 shadow-lg shadow-cyan-900/30 lg:grid-cols-[1.1fr,0.9fr]"
      >
        <div className="space-y-3">
          <p className="text-xs uppercase tracking-[0.3em] text-cyan-300">Custom build desk</p>
          <h3 className="text-2xl font-semibold text-white">Tell us your playstyle, we’ll spec it right</h3>
          <p className="text-slate-300">
            We pair you with a builder who understands your games, tools, and budget. Expect a parts list with rationale,
            thermal model, and upgrade path—before we ever charge you.
          </p>
          <ul className="grid gap-2 text-sm text-slate-300">
            <li>• Live parts approval and pricing transparency.</li>
            <li>• Noise, thermals, and aesthetics tuned to your preferences.</li>
            <li>• Burn-in report and cable map in your delivery packet.</li>
          </ul>
        </div>
        <form onSubmit={handleSubmit} className="flex flex-col gap-3 rounded-2xl border border-slate-800 bg-slate-950/70 p-6">
          <div className="flex items-center justify-between">
            <p className="text-base font-semibold text-white">Request a custom quote</p>
            {formStatus === "success" && (
              <span className="text-sm font-semibold text-emerald-300">Sent!</span>
            )}
            {formStatus === "error" && (
              <span className="text-sm font-semibold text-rose-300">Try again</span>
            )}
          </div>
          <label className="text-sm text-slate-200">
            Name
            <input
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-white focus:border-cyan-400 focus:outline-none"
            />
          </label>
          <label className="text-sm text-slate-200">
            Email
            <input
              required
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-white focus:border-cyan-400 focus:outline-none"
            />
          </label>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="text-sm text-slate-200">
              Budget (USD)
              <input
                type="number"
                min="500"
                value={form.budget}
                onChange={(e) => setForm({ ...form, budget: e.target.value })}
                className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-white focus:border-cyan-400 focus:outline-none"
              />
            </label>
            <label className="text-sm text-slate-200">
              Primary use
              <input
                placeholder="4K gaming, streaming, CAD, AI..."
                value={form.primary_use}
                onChange={(e) => setForm({ ...form, primary_use: e.target.value })}
                className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-white focus:border-cyan-400 focus:outline-none"
              />
            </label>
          </div>
          <label className="text-sm text-slate-200">
            Preferences
            <textarea
              rows={4}
              placeholder="Case size, noise level, RGB, favorite games, render workloads..."
              value={form.preferences}
              onChange={(e) => setForm({ ...form, preferences: e.target.value })}
              className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-white focus:border-cyan-400 focus:outline-none"
            />
          </label>
          <button
            type="submit"
            disabled={formStatus === "sending"}
            className="mt-2 inline-flex items-center justify-center rounded-lg bg-gradient-to-r from-cyan-400 to-blue-600 px-4 py-2 text-sm font-semibold text-slate-900 transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {formStatus === "sending" ? "Sending..." : "Send my build brief"}
          </button>
          <p className="text-xs text-slate-500">
            We respond within one business day with a parts list, quote, and ETA.
          </p>
        </form>
      </section>

      <section id="about" className="grid gap-6 rounded-3xl border border-slate-800 bg-slate-900/70 p-8 shadow-lg shadow-cyan-900/30 lg:grid-cols-[1.1fr,0.9fr]">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-cyan-300">About WhatAPC</p>
          <h3 className="mt-2 text-2xl font-semibold text-white">Builders who publish every detail</h3>
          <p className="mt-3 text-slate-300">
            We’re a small, obsessive crew of PC builders, thermal nerds, and gamers. Every rig ships with a burn-in
            report, cable map, BIOS profile, and part serials—so you always know what you own and how to upgrade.
          </p>
        </div>
        <div className="grid gap-3 text-sm text-slate-200">
          {[
            "Burn-in: 24h CPU + GPU + memory stability testing.",
            "Performance: Per-game benchmarks on your primary titles.",
            "Logistics: Foam-packed, GPU bracketed, insured shipping nationwide.",
            "Support: Remote tune-ups, driver sanity checks, and upgrade planning.",
          ].map((item) => (
            <div key={item} className="rounded-xl border border-slate-800 bg-slate-950/70 px-4 py-3">
              {item}
            </div>
          ))}
        </div>
      </section>

      <section id="faq" className="space-y-4">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-cyan-300">FAQ</p>
          <h3 className="text-2xl font-semibold text-white">Answers before you click buy</h3>
        </div>
        <div className="grid gap-3 md:grid-cols-2">
          {faqs.map((faq) => (
            <FAQ key={faq.id} item={faq} />
          ))}
        </div>
      </section>

      <footer className="rounded-2xl border border-slate-800 bg-slate-900/70 p-8 text-sm text-slate-300">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-cyan-300">WhatAPC</p>
            <p className="text-base font-semibold text-white">Custom, transparent, ready to ship.</p>
          </div>
          <div className="flex gap-3">
            <a className="rounded-lg border border-slate-800 px-3 py-2 text-slate-200 hover:border-cyan-400/70 hover:text-white" href="#catalog">
              Browse builds
            </a>
            <a className="rounded-lg bg-gradient-to-r from-cyan-400 to-blue-600 px-3 py-2 font-semibold text-slate-900 hover:brightness-105" href="#custom">
              Request custom
            </a>
          </div>
        </div>
        <p className="mt-4 text-xs text-slate-500">
          Built by humans who play, create, and benchmark. We’re here when you need us.
        </p>
      </footer>
    </div>
  );
}

export default App;
